import React, { useState, useMemo, useCallback, useRef } from 'react';
import { BarChart2, Trash2, Download, Loader2, ChevronDown, ZoomIn, RotateCcw, FileText } from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, ReferenceLine, ReferenceArea, Area, ComposedChart
} from 'recharts';
import { useSSDResults, useSSDResultTimeseries, useDeleteSSDResult } from '../../api/hooks';
import type { SpillEvent } from '../../api/hooks';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface ResultsTabProps {
    projectId: number;
}

const ResultsTab: React.FC<ResultsTabProps> = ({ projectId }) => {
    const { data: results, isLoading } = useSSDResults(projectId);
    const [selectedResultId, setSelectedResultId] = useState<number | null>(null);
    const [downsampleFactor, setDownsampleFactor] = useState(1000);

    // Zoom state - ISO date strings for backend query
    const [zoomStart, setZoomStart] = useState<string | null>(null);
    const [zoomEnd, setZoomEnd] = useState<string | null>(null);

    // Click selection state for interactive chart zoom
    const [clickStart, setClickStart] = useState<string | null>(null);
    const [isSelectingZoom, setIsSelectingZoom] = useState(false);

    const deleteResultMutation = useDeleteSSDResult();

    // Auto-select the most recent result
    React.useEffect(() => {
        if (results && results.length > 0 && !selectedResultId) {
            setSelectedResultId(results[0].id);
        }
    }, [results, selectedResultId]);

    // Reset zoom when result changes
    React.useEffect(() => {
        setZoomStart(null);
        setZoomEnd(null);
        setClickStart(null);
        setIsSelectingZoom(false);
    }, [selectedResultId]);

    const selectedResult = useMemo(() => {
        return results?.find(r => r.id === selectedResultId) || null;
    }, [results, selectedResultId]);

    // Pass zoom range to hook for server-side filtering
    const { data: timeseriesData, isLoading: tsLoading } = useSSDResultTimeseries(
        projectId,
        selectedResultId,
        downsampleFactor,
        zoomStart,
        zoomEnd
    );

    const handleDelete = async (resultId: number) => {
        if (!confirm('Delete this analysis result? This cannot be undone.')) return;
        await deleteResultMutation.mutateAsync({ projectId, resultId });
        if (selectedResultId === resultId) {
            setSelectedResultId(null);
        }
    };

    const exportToCSV = () => {
        if (!selectedResult) return;

        const headers = ['Start Time', 'End Time', 'Duration (h)', 'Volume (m³)', 'Peak Flow (m³/s)', 'Bathing Season'];
        const rows = selectedResult.spill_events.map((e: SpillEvent) => [
            e.start_time, e.end_time, e.duration_hours, e.volume_m3, e.peak_flow_m3s, e.is_bathing_season
        ]);

        const csv = [headers.join(','), ...rows.map((r: (string | number | boolean)[]) => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedResult.scenario_name}_spill_events.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // State for PDF generation
    const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
    const chartsContainerRef = useRef<HTMLDivElement>(null);

    const exportToPDF = async () => {
        if (!selectedResult) return;
        setIsGeneratingPDF(true);

        try {
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();
            const margin = 15;
            const contentWidth = pageWidth - 2 * margin;
            let yPos = margin;

            // Helper to add page header
            const addHeader = () => {
                pdf.setFontSize(8);
                pdf.setTextColor(128);
                pdf.text(`SSD Analysis Report - ${selectedResult.scenario_name}`, margin, 8);
                pdf.text(new Date().toLocaleDateString(), pageWidth - margin - 20, 8);
                pdf.setDrawColor(200);
                pdf.line(margin, 10, pageWidth - margin, 10);
            };

            // Helper to check and add new page
            const checkNewPage = (requiredSpace: number) => {
                if (yPos + requiredSpace > pageHeight - margin) {
                    pdf.addPage();
                    addHeader();
                    yPos = 20;
                    return true;
                }
                return false;
            };

            // Page 1: Summary
            addHeader();
            yPos = 20;

            // Title
            pdf.setFontSize(20);
            pdf.setTextColor(0);
            pdf.text('Storage Analysis Report', margin, yPos);
            yPos += 12;

            // Scenario details
            pdf.setFontSize(12);
            pdf.setTextColor(80);
            pdf.text(`Scenario: ${selectedResult.scenario_name}`, margin, yPos);
            yPos += 7;
            pdf.text(`CSO Asset: ${selectedResult.cso_name}`, margin, yPos);
            yPos += 7;
            pdf.text(`Configuration: ${selectedResult.config_name}`, margin, yPos);
            yPos += 7;
            pdf.text(`Analysis Date: ${new Date(selectedResult.analysis_date).toLocaleString()}`, margin, yPos);
            yPos += 7;
            pdf.text(`Period: ${new Date(selectedResult.start_date).toLocaleDateString()} - ${new Date(selectedResult.end_date).toLocaleDateString()}`, margin, yPos);
            yPos += 15;

            // Key Metrics box
            pdf.setFillColor(255, 247, 237); // Orange-50
            pdf.roundedRect(margin, yPos, contentWidth, 35, 3, 3, 'F');
            yPos += 8;

            pdf.setFontSize(10);
            pdf.setTextColor(100);
            const col1 = margin + 5;
            const col2 = margin + contentWidth / 4;
            const col3 = margin + contentWidth / 2;
            const col4 = margin + 3 * contentWidth / 4;

            pdf.text('Required Storage', col1, yPos);
            pdf.text('Total Spills', col2, yPos);
            pdf.text('Bathing Spills', col3, yPos);
            pdf.text('Status', col4, yPos);
            yPos += 8;

            pdf.setFontSize(16);
            pdf.setTextColor(0);
            pdf.text(`${selectedResult.final_storage_m3.toLocaleString()} m³`, col1, yPos);
            pdf.text(`${selectedResult.spill_count}`, col2, yPos);
            pdf.text(`${selectedResult.bathing_spill_count}`, col3, yPos);
            pdf.text(selectedResult.converged ? '✓ Converged' : '○ Not Converged', col4, yPos);
            yPos += 10;

            pdf.setFontSize(8);
            pdf.setTextColor(120);
            pdf.text(`Target: ${selectedResult.spill_target} spills/year`, col1, yPos);
            pdf.text(`Iterations: ${selectedResult.iterations}`, col2, yPos);
            yPos += 20;

            // Additional stats
            pdf.setFontSize(11);
            pdf.setTextColor(60);
            pdf.text('Additional Statistics', margin, yPos);
            yPos += 8;

            pdf.setFontSize(10);
            pdf.setTextColor(80);
            pdf.text(`Total Spill Volume: ${selectedResult.total_spill_volume_m3.toLocaleString()} m³`, margin, yPos);
            yPos += 6;
            pdf.text(`Total Spill Duration: ${selectedResult.total_spill_duration_hours.toFixed(1)} hours`, margin, yPos);
            yPos += 6;
            pdf.text(`PFF Increase: ${selectedResult.pff_increase} m³/s`, margin, yPos);
            yPos += 6;
            pdf.text(`Tank Volume: ${(selectedResult.tank_volume || 0).toLocaleString()} m³`, margin, yPos);

            // Page 2: Charts in LANDSCAPE
            if (chartsContainerRef.current) {
                pdf.addPage('l'); // 'l' for landscape
                const landscapeWidth = pdf.internal.pageSize.getWidth();
                const landscapeHeight = pdf.internal.pageSize.getHeight();
                const landscapeContentWidth = landscapeWidth - 2 * margin;

                // Landscape header
                pdf.setFontSize(8);
                pdf.setTextColor(128);
                pdf.text(`SSD Analysis Report - ${selectedResult.scenario_name}`, margin, 8);
                pdf.text(new Date().toLocaleDateString(), landscapeWidth - margin - 20, 8);
                pdf.setDrawColor(200);
                pdf.line(margin, 10, landscapeWidth - margin, 10);

                yPos = 20;
                pdf.setFontSize(14);
                pdf.setTextColor(60);
                pdf.text('Time Series Charts', margin, yPos);
                yPos += 10;

                try {
                    const canvas = await html2canvas(chartsContainerRef.current, {
                        scale: 2,
                        backgroundColor: '#ffffff',
                        logging: false,
                    });
                    const imgData = canvas.toDataURL('image/png');
                    const imgWidth = landscapeContentWidth;
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;

                    // Fit to page
                    const maxImgHeight = landscapeHeight - yPos - margin;
                    const finalHeight = Math.min(imgHeight, maxImgHeight);
                    const finalWidth = (finalHeight / imgHeight) * imgWidth;

                    pdf.addImage(imgData, 'PNG', margin, yPos, finalWidth, finalHeight);
                } catch (chartErr) {
                    console.warn('Could not capture charts:', chartErr);
                    pdf.setFontSize(9);
                    pdf.setTextColor(150);
                    pdf.text('Charts could not be captured.', margin, yPos);
                }
            }

            // Page 3+: Spill Events Table in PORTRAIT
            if (selectedResult.spill_events.length > 0) {
                pdf.addPage('p'); // 'p' for portrait
                const portraitWidth = pdf.internal.pageSize.getWidth();
                const portraitHeight = pdf.internal.pageSize.getHeight();
                const portraitContentWidth = portraitWidth - 2 * margin;

                // Portrait header helper for this section
                const addPortraitHeader = () => {
                    pdf.setFontSize(8);
                    pdf.setTextColor(128);
                    pdf.text(`SSD Analysis Report - ${selectedResult.scenario_name}`, margin, 8);
                    pdf.text(new Date().toLocaleDateString(), portraitWidth - margin - 20, 8);
                    pdf.setDrawColor(200);
                    pdf.line(margin, 10, portraitWidth - margin, 10);
                };

                addPortraitHeader();
                yPos = 20;

                pdf.setFontSize(14);
                pdf.setTextColor(60);
                pdf.text(`Spill Events (${selectedResult.spill_events.length} total)`, margin, yPos);
                yPos += 10;

                // Table header
                const colWidths = [45, 45, 25, 30, 25, 20];
                const headers = ['Start Time', 'End Time', 'Duration (h)', 'Volume (m³)', 'Peak (m³/s)', 'Bathing'];

                const drawTableHeader = () => {
                    pdf.setFillColor(245, 245, 245);
                    pdf.rect(margin, yPos - 4, portraitContentWidth, 8, 'F');
                    pdf.setFontSize(8);
                    pdf.setTextColor(80);
                    let xPos = margin + 2;
                    headers.forEach((header, i) => {
                        pdf.text(header, xPos, yPos);
                        xPos += colWidths[i];
                    });
                    yPos += 6;
                };

                drawTableHeader();

                // Table rows
                pdf.setTextColor(60);
                const rowHeight = 5;

                selectedResult.spill_events.forEach((event: SpillEvent, idx: number) => {
                    // Check if need new page
                    if (yPos + rowHeight + 5 > portraitHeight - margin) {
                        pdf.addPage('p');
                        addPortraitHeader();
                        yPos = 20;
                        drawTableHeader();
                    }

                    // Alternate row background
                    if (idx % 2 === 0) {
                        pdf.setFillColor(252, 252, 252);
                        pdf.rect(margin, yPos - 3, portraitContentWidth, rowHeight, 'F');
                    }

                    pdf.setTextColor(60);
                    let rxPos = margin + 2;
                    const startDate = new Date(event.start_time).toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' });
                    const endDate = new Date(event.end_time).toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' });

                    pdf.text(startDate, rxPos, yPos); rxPos += colWidths[0];
                    pdf.text(endDate, rxPos, yPos); rxPos += colWidths[1];
                    pdf.text(event.duration_hours.toFixed(2), rxPos, yPos); rxPos += colWidths[2];
                    pdf.text(event.volume_m3.toFixed(1), rxPos, yPos); rxPos += colWidths[3];
                    pdf.text(event.peak_flow_m3s.toFixed(4), rxPos, yPos); rxPos += colWidths[4];
                    pdf.text(event.is_bathing_season ? 'Yes' : '', rxPos, yPos);

                    yPos += rowHeight;
                });
            } else {
                // No spill events - still add a portrait page
                pdf.addPage('p');
                addHeader();
                yPos = 30;
                pdf.setFontSize(10);
                pdf.setTextColor(34, 139, 34); // Green
                pdf.text('No spill events recorded - storage solution eliminates all spills.', margin, yPos);
            }

            // Save PDF
            pdf.save(`${selectedResult.scenario_name}_report.pdf`);
        } catch (err) {
            console.error('PDF generation failed:', err);
            alert('Failed to generate PDF. Please try again.');
        } finally {
            setIsGeneratingPDF(false);
        }
    };

    // Format chart data - must be before handleChartClick
    const formatChartData = useMemo(() => {
        if (!timeseriesData?.data) return [];
        return timeseriesData.data.map((d: Record<string, unknown>) => ({
            ...d,
            Time: new Date(String(d.Time)).toLocaleDateString('en-GB', {
                day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
            }),
            _rawTime: d.Time // Keep original for click detection
        }));
    }, [timeseriesData]);

    // Handle chart click for zoom selection
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleChartClick = useCallback((data: any) => {
        // console.log('Chart clicked:', data);

        // Use activeIndex to find the data point
        if (data.activeIndex === undefined || data.activeIndex === null) {
            // console.log('No activeIndex in click data');
            return;
        }

        const index = typeof data.activeIndex === 'string' ? parseInt(data.activeIndex, 10) : data.activeIndex;
        const clickedPoint = formatChartData[index];

        if (!clickedPoint) {
            // console.log('No data point at index:', index);
            return;
        }

        const rawTime = clickedPoint._rawTime as string;
        // console.log('Clicked index:', index, 'rawTime:', rawTime);

        if (!rawTime) {
            // console.log('No _rawTime in data point');
            return;
        }

        if (!isSelectingZoom) {
            // First click - set start
            // console.log('Setting zoom start:', rawTime);
            setClickStart(rawTime);
            setIsSelectingZoom(true);
        } else {
            // Second click - set end and apply zoom
            const start = clickStart!;
            const end = rawTime;
            // console.log('Setting zoom end:', end, 'start was:', start);

            // Ensure start < end
            if (new Date(start) > new Date(end)) {
                setZoomStart(end);
                setZoomEnd(start);
            } else {
                setZoomStart(start);
                setZoomEnd(end);
            }

            setClickStart(null);
            setIsSelectingZoom(false);
        }
    }, [isSelectingZoom, clickStart, formatChartData]);

    // Reset zoom
    const handleResetZoom = useCallback(() => {
        setZoomStart(null);
        setZoomEnd(null);
        setClickStart(null);
        setIsSelectingZoom(false);
    }, []);

    // Cancel zoom selection
    const handleCancelSelection = useCallback(() => {
        setClickStart(null);
        setIsSelectingZoom(false);
    }, []);

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-orange-500" size={32} />
            </div>
        );
    }

    if (!results || results.length === 0) {
        return (
            <div className="text-center py-16 text-gray-400">
                <BarChart2 size={64} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg">No analysis results yet</p>
                <p className="text-sm mt-2">Run an analysis from the Analysis tab to see results here.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Result Selector */}
            <div className="flex items-center gap-4 flex-wrap">
                <div className="flex-1 min-w-[200px]">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Select Result</label>
                    <div className="relative">
                        <select
                            value={selectedResultId || ''}
                            onChange={(e) => setSelectedResultId(Number(e.target.value))}
                            className="block w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 pr-10 text-gray-900 focus:border-orange-500 focus:ring-orange-500 appearance-none"
                        >
                            {results.map((result) => (
                                <option key={result.id} value={result.id}>
                                    {result.scenario_name} — {result.cso_name} ({new Date(result.analysis_date).toLocaleDateString()})
                                </option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={18} />
                    </div>
                </div>

                <div className="flex gap-2 pt-6">
                    <button
                        onClick={exportToPDF}
                        disabled={!selectedResult || isGeneratingPDF}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {isGeneratingPDF ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <FileText size={16} />
                        )}
                        Export PDF
                    </button>
                    <button
                        onClick={exportToCSV}
                        disabled={!selectedResult}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50"
                    >
                        <Download size={16} />
                        Export CSV
                    </button>
                    <button
                        onClick={() => selectedResultId && handleDelete(selectedResultId)}
                        disabled={!selectedResultId || deleteResultMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors disabled:opacity-50"
                    >
                        <Trash2 size={16} />
                        Delete
                    </button>
                </div>
            </div>

            {selectedResult && (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 text-center">
                            <p className="text-3xl font-bold text-orange-700">{selectedResult.final_storage_m3.toLocaleString()}</p>
                            <p className="text-sm text-orange-600 mt-1">Required Storage (m³)</p>
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 text-center">
                            <p className="text-3xl font-bold text-blue-700">{selectedResult.spill_count}</p>
                            <p className="text-sm text-blue-600 mt-1">Total Spills</p>
                        </div>
                        {selectedResult.spill_target_bathing && selectedResult.spill_target_bathing > 0 ? (
                            <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-5 text-center">
                                <p className="text-3xl font-bold text-cyan-700">{selectedResult.bathing_spill_count}</p>
                                <p className="text-sm text-cyan-600 mt-1">Bathing Season Spills</p>
                            </div>
                        ) : (
                            <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 text-center">
                                <p className="text-3xl font-bold text-gray-400">N/A</p>
                                <p className="text-sm text-gray-400 mt-1">Bathing Season Spills</p>
                            </div>
                        )}
                        <div className={`${selectedResult.converged ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'} border rounded-xl p-5 text-center`}>
                            <p className={`text-3xl font-bold ${selectedResult.converged ? 'text-green-700' : 'text-amber-700'}`}>
                                {selectedResult.converged ? '✓' : '○'}
                            </p>
                            <p className={`text-sm mt-1 ${selectedResult.converged ? 'text-green-600' : 'text-amber-600'}`}>
                                {selectedResult.converged ? `Converged (${selectedResult.iterations} iter)` : 'Not Converged'}
                            </p>
                        </div>
                    </div>

                    {/* Additional Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500">CSO Name</p>
                            <p className="font-semibold text-gray-900">{selectedResult.cso_name}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500">Total Spill Volume</p>
                            <p className="font-semibold text-gray-900">{selectedResult.total_spill_volume_m3.toLocaleString()} m³</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500">Total Spill Duration</p>
                            <p className="font-semibold text-gray-900">{selectedResult.total_spill_duration_hours.toFixed(1)} hours</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500">Spill Target</p>
                            <p className="font-semibold text-gray-900">{selectedResult.spill_target} per annum</p>
                        </div>
                    </div>

                    {/* Charts Section */}
                    <div ref={chartsContainerRef} className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex flex-col gap-4 mb-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-gray-900">Time Series Charts</h3>
                                <div className="flex items-center gap-2">
                                    <label className="text-sm text-gray-600">Resolution:</label>
                                    <select
                                        value={downsampleFactor}
                                        onChange={(e) => setDownsampleFactor(Number(e.target.value))}
                                        className="text-sm border border-gray-300 rounded px-2 py-1"
                                    >
                                        <option value={1}>Full (all points)</option>
                                        <option value={500}>Fast (~500 points)</option>
                                        <option value={1000}>Medium (~1000 points)</option>
                                        <option value={2000}>Detailed (~2000 points)</option>
                                        <option value={5000}>High (~5000 points)</option>
                                    </select>
                                </div>
                            </div>

                            {/* Zoom Controls */}
                            <div className="flex flex-wrap items-center gap-4 p-3 bg-gray-50 rounded-lg border">
                                <div className="flex items-center gap-2">
                                    <ZoomIn size={16} className="text-gray-500" />
                                    <span className="text-sm font-medium text-gray-700">Zoom:</span>
                                </div>

                                <div className="flex items-center gap-2">
                                    <label className="text-xs text-gray-500">From:</label>
                                    <input
                                        type="datetime-local"
                                        value={zoomStart ? zoomStart.slice(0, 16) : ''}
                                        onChange={(e) => setZoomStart(e.target.value ? new Date(e.target.value).toISOString() : null)}
                                        className="text-sm border border-gray-300 rounded px-2 py-1"
                                    />
                                </div>

                                <div className="flex items-center gap-2">
                                    <label className="text-xs text-gray-500">To:</label>
                                    <input
                                        type="datetime-local"
                                        value={zoomEnd ? zoomEnd.slice(0, 16) : ''}
                                        onChange={(e) => setZoomEnd(e.target.value ? new Date(e.target.value).toISOString() : null)}
                                        className="text-sm border border-gray-300 rounded px-2 py-1"
                                    />
                                </div>

                                {(zoomStart || zoomEnd) && (
                                    <button
                                        onClick={handleResetZoom}
                                        className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition-colors"
                                    >
                                        <RotateCcw size={14} />
                                        Reset
                                    </button>
                                )}

                                {isSelectingZoom && (
                                    <>
                                        <span className="text-sm text-orange-600 font-medium animate-pulse">
                                            Click chart to set end point
                                        </span>
                                        <button
                                            onClick={handleCancelSelection}
                                            className="text-sm text-gray-500 hover:text-gray-700 underline"
                                        >
                                            Cancel
                                        </button>
                                    </>
                                )}

                                {!isSelectingZoom && !zoomStart && !zoomEnd && (
                                    <span className="text-xs text-gray-500">
                                        Click on chart twice to zoom, or use date pickers
                                    </span>
                                )}
                            </div>
                        </div>

                        {tsLoading ? (
                            <div className="flex justify-center items-center h-64">
                                <Loader2 className="animate-spin text-orange-500" size={24} />
                                <span className="ml-2 text-gray-500">Loading chart data...</span>
                            </div>
                        ) : timeseriesData ? (
                            <div className="space-y-1">
                                {/* Chart 1: Continuation Flow */}
                                {(timeseriesData.columns.includes('Cont_Flow_Original') ||
                                    timeseriesData.columns.some(c => !['Time', 'CSO_Flow_Original', 'Spill_Flow', 'Tank_Volume'].includes(c))) && (
                                        <div>
                                            <h4 className="text-sm font-medium text-gray-700 mb-1">Continuation Flow</h4>
                                            <ResponsiveContainer width="100%" height={160}>
                                                <LineChart data={formatChartData} onClick={handleChartClick} style={{ cursor: 'crosshair' }}>
                                                    <CartesianGrid strokeDasharray="3 3" />
                                                    <XAxis dataKey="Time" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                                                    <YAxis tick={{ fontSize: 10 }} label={{ value: 'm³/s', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                                                    <Tooltip />
                                                    <Legend />
                                                    {timeseriesData.columns.includes('Cont_Flow_Original') && (
                                                        <Line
                                                            type="monotone"
                                                            dataKey="Cont_Flow_Original"
                                                            stroke="#ef4444"
                                                            name="Before Storage"
                                                            dot={false}
                                                            strokeWidth={1}
                                                        />
                                                    )}
                                                    {timeseriesData.columns
                                                        .filter(c => !['Time', 'CSO_Flow_Original', 'Cont_Flow_Original', 'Spill_Flow', 'Tank_Volume'].includes(c))
                                                        .slice(0, 1)
                                                        .map(col => (
                                                            <Line
                                                                key={col}
                                                                type="monotone"
                                                                dataKey={col}
                                                                stroke="#3b82f6"
                                                                name="After Storage"
                                                                dot={false}
                                                                strokeWidth={1}
                                                            />
                                                        ))}
                                                    <ReferenceLine y={0} stroke="#000" />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                    )}

                                {/* Chart 2: Spill Flow */}
                                <div>
                                    <h4 className="text-sm font-medium text-gray-700 mb-1">Spill Flow</h4>
                                    <ResponsiveContainer width="100%" height={180}>
                                        <ComposedChart data={formatChartData} onClick={handleChartClick} style={{ cursor: 'crosshair' }}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="Time" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                                            <YAxis tick={{ fontSize: 10 }} label={{ value: 'm³/s', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                                            <Tooltip />
                                            <Legend />

                                            {/* Spill event blocks */}
                                            {selectedResult?.spill_events?.map((spill: SpillEvent, idx: number) => {
                                                const startTime = new Date(spill.start_time).toLocaleDateString('en-GB', {
                                                    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
                                                });
                                                const endTime = new Date(spill.end_time).toLocaleDateString('en-GB', {
                                                    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
                                                });
                                                const color = spill.duration_hours <= 12 ? '#3b82f6' : '#06b6d4';
                                                return (
                                                    <ReferenceArea
                                                        key={idx}
                                                        x1={startTime}
                                                        x2={endTime}
                                                        fill={color}
                                                        fillOpacity={0.15}
                                                        stroke={color}
                                                        strokeOpacity={0.3}
                                                    />
                                                );
                                            })}

                                            {timeseriesData.columns.includes('CSO_Flow_Original') && (
                                                <Line
                                                    type="monotone"
                                                    dataKey="CSO_Flow_Original"
                                                    stroke="#ef4444"
                                                    name="Before Storage"
                                                    dot={false}
                                                    strokeWidth={1}
                                                />
                                            )}
                                            {timeseriesData.columns.includes('Spill_Flow') && (
                                                <Line
                                                    type="monotone"
                                                    dataKey="Spill_Flow"
                                                    stroke="#3b82f6"
                                                    name="After Storage"
                                                    dot={false}
                                                    strokeWidth={1}
                                                />
                                            )}
                                            <ReferenceLine y={0} stroke="#000" />
                                        </ComposedChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Chart 3: Tank Volume with Capacity Line */}
                                {timeseriesData.columns.includes('Tank_Volume') && selectedResult && (
                                    <div>
                                        <h4 className="text-sm font-medium text-gray-700 mb-1">Tank Volume</h4>
                                        <ResponsiveContainer width="100%" height={180}>
                                            <ComposedChart data={formatChartData} onClick={handleChartClick} style={{ cursor: 'crosshair' }}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="Time" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                                                <YAxis
                                                    tick={{ fontSize: 10 }}
                                                    label={{ value: 'm³', angle: -90, position: 'insideLeft', fontSize: 10 }}
                                                    domain={[0, Math.ceil(selectedResult.final_storage_m3 * 1.1)]}
                                                />
                                                <Tooltip />
                                                <Legend verticalAlign="top" height={20} />

                                                <Area
                                                    type="monotone"
                                                    dataKey="Tank_Volume"
                                                    fill="#22c55e"
                                                    fillOpacity={0.3}
                                                    stroke="#22c55e"
                                                    strokeWidth={1.5}
                                                    name="Tank Volume"
                                                />

                                                <ReferenceLine
                                                    y={selectedResult.final_storage_m3}
                                                    stroke="#f97316"
                                                    strokeDasharray="5 5"
                                                    strokeWidth={2}
                                                    label={{
                                                        value: `Capacity: ${selectedResult.final_storage_m3.toLocaleString()} m³`,
                                                        position: 'right',
                                                        fill: '#f97316',
                                                        fontSize: 10
                                                    }}
                                                />

                                            </ComposedChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}

                                <p className="text-xs text-gray-500 text-right mt-2">
                                    Showing {timeseriesData.total_points.toLocaleString()} points
                                    {timeseriesData.downsampled && ` (downsampled from ${timeseriesData.original_points?.toLocaleString() || 'full dataset'})`}
                                </p>
                            </div>
                        ) : (
                            <p className="text-gray-500 text-center py-8">No time-series data available for this result.</p>
                        )}
                    </div>

                    {/* Spill Events Table */}
                    {selectedResult.spill_events.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                Spill Events ({selectedResult.spill_events.length})
                            </h3>
                            <div className="border border-gray-200 rounded-xl overflow-hidden">
                                <div className="overflow-auto max-h-96">
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-gray-600 font-medium">#</th>
                                                <th className="px-4 py-3 text-left text-gray-600 font-medium">Start Time</th>
                                                <th className="px-4 py-3 text-left text-gray-600 font-medium">End Time</th>
                                                <th className="px-4 py-3 text-right text-gray-600 font-medium">Duration (h)</th>
                                                <th className="px-4 py-3 text-right text-gray-600 font-medium">Volume (m³)</th>
                                                <th className="px-4 py-3 text-right text-gray-600 font-medium">Peak Flow (m³/s)</th>
                                                <th className="px-4 py-3 text-center text-gray-600 font-medium">Bathing</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {selectedResult.spill_events.map((event: SpillEvent, idx: number) => (
                                                <tr key={idx} className={event.is_bathing_season ? 'bg-cyan-50/50' : 'hover:bg-gray-50'}>
                                                    <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                                                    <td className="px-4 py-3 text-gray-700">
                                                        {new Date(event.start_time).toLocaleString()}
                                                    </td>
                                                    <td className="px-4 py-3 text-gray-700">
                                                        {new Date(event.end_time).toLocaleString()}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-gray-700">
                                                        {event.duration_hours.toFixed(2)}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-gray-700">
                                                        {event.volume_m3.toFixed(1)}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-gray-700">
                                                        {event.peak_flow_m3s.toFixed(4)}
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        {event.is_bathing_season && (
                                                            <span className="inline-block w-3 h-3 bg-cyan-500 rounded-full" title="Bathing Season" />
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {selectedResult.spill_events.length === 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                            <p className="text-green-700 font-medium">No spill events recorded</p>
                            <p className="text-green-600 text-sm mt-1">The storage solution eliminates all spills for this configuration.</p>
                        </div>
                    )}
                </>
            )}

            {/* Summary Table - All Results */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">All Saved Results</h3>
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                    <div className="overflow-auto">
                        <table className="min-w-full text-sm">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-gray-600 font-medium">Scenario</th>
                                    <th className="px-4 py-3 text-left text-gray-600 font-medium">CSO</th>
                                    <th className="px-4 py-3 text-left text-gray-600 font-medium">Config</th>
                                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Storage (m³)</th>
                                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Spills</th>
                                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Bathing</th>
                                    <th className="px-4 py-3 text-center text-gray-600 font-medium">Status</th>
                                    <th className="px-4 py-3 text-left text-gray-600 font-medium">Date</th>
                                    <th className="px-4 py-3"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {results.map((result) => (
                                    <tr
                                        key={result.id}
                                        className={`cursor-pointer ${result.id === selectedResultId ? 'bg-orange-50' : 'hover:bg-gray-50'}`}
                                        onClick={() => setSelectedResultId(result.id)}
                                    >
                                        <td className="px-4 py-3 font-medium text-gray-900">{result.scenario_name}</td>
                                        <td className="px-4 py-3 text-gray-700">{result.cso_name}</td>
                                        <td className="px-4 py-3 text-gray-700">{result.config_name}</td>
                                        <td className="px-4 py-3 text-right text-gray-700">{result.final_storage_m3.toLocaleString()}</td>
                                        <td className="px-4 py-3 text-right text-gray-700">{result.spill_count}</td>
                                        <td className="px-4 py-3 text-right text-gray-700">
                                            {result.spill_target_bathing && result.spill_target_bathing > 0
                                                ? result.bathing_spill_count
                                                : <span className="text-gray-400">N/A</span>}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${result.converged
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-amber-100 text-amber-800'
                                                }`}>
                                                {result.converged ? 'Converged' : 'Not Converged'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-gray-500 text-xs">
                                            {new Date(result.analysis_date).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDelete(result.id);
                                                }}
                                                className="text-red-500 hover:text-red-700 p-1"
                                                title="Delete result"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResultsTab;
