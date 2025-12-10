import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Play, Loader2, CheckCircle, AlertTriangle, XCircle, Square, CheckSquare, Layers, Terminal, Trash2, Clock } from 'lucide-react';
import {
    useSSDScenarios, useSSDCSOAssets, useSSDAnalysisConfigs, useSSDFiles, useSSDResults,
} from '../../api/hooks';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnalysisResult = any;  // Full result type from API

interface AnalysisTabProps {
    projectId: number;
    onRunAnalysis: (scenarioIds: number[]) => Promise<AnalysisResult>;
    isRunning: boolean;
}

interface PreflightCheck {
    label: string;
    passed: boolean;
    detail?: string;
    critical: boolean;
}

interface LogEntry {
    timestamp: Date;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
}

const AnalysisTab: React.FC<AnalysisTabProps> = ({ projectId, onRunAnalysis, isRunning }) => {
    const { data: files, isLoading: filesLoading } = useSSDFiles(projectId);
    const { data: csoAssets, isLoading: assetsLoading } = useSSDCSOAssets(projectId);
    const { data: configs, isLoading: configsLoading } = useSSDAnalysisConfigs(projectId);
    const { data: scenarios, isLoading: scenariosLoading } = useSSDScenarios(projectId);
    const { data: savedResults } = useSSDResults(projectId);

    const [selectedScenarios, setSelectedScenarios] = useState<Set<number>>(new Set());
    const [analysisLog, setAnalysisLog] = useState<LogEntry[]>([]);
    const logEndRef = useRef<HTMLDivElement>(null);

    const isLoading = filesLoading || assetsLoading || configsLoading || scenariosLoading;

    // Auto-scroll log to bottom when new entries added
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [analysisLog]);

    // Add log entry helper
    const addLog = (message: string, type: LogEntry['type'] = 'info') => {
        setAnalysisLog(prev => [...prev, { timestamp: new Date(), message, type }]);
    };

    // Clear log
    const clearLog = () => {
        setAnalysisLog([]);
    };

    // Pre-flight checks
    const preflightChecks: PreflightCheck[] = [
        {
            label: 'Data files uploaded',
            passed: (files?.length || 0) > 0,
            detail: files?.length ? `${files.length} file(s) available` : 'Upload CSV data in Data Import tab',
            critical: true,
        },
        {
            label: 'CSO assets defined',
            passed: (csoAssets?.length || 0) > 0,
            detail: csoAssets?.length ? `${csoAssets.length} CSO asset(s) defined` : 'Create CSO assets in CSO Assets tab',
            critical: true,
        },
        {
            label: 'Analysis configurations created',
            passed: (configs?.length || 0) > 0,
            detail: configs?.length ? `${configs.length} configuration(s) available` : 'Create configurations in Analysis Configs tab',
            critical: true,
        },
        {
            label: 'Analysis scenarios defined',
            passed: (scenarios?.length || 0) > 0,
            detail: scenarios?.length ? `${scenarios.length} scenario(s) ready to run` : 'Create scenarios in Analysis Scenarios tab',
            critical: true,
        },
    ];

    const allChecksPassed = preflightChecks.every(c => c.passed);
    const readyToRun = allChecksPassed && selectedScenarios.size > 0;

    // Helper to get CSO asset name by ID
    const getCSOName = (id: number): string => {
        return csoAssets?.find(a => a.id === id)?.name || `CSO #${id}`;
    };

    // Helper to get config name by ID
    const getConfigName = (id: number): string => {
        return configs?.find(c => c.id === id)?.name || `Config #${id}`;
    };

    // Helper to get latest result for a scenario
    const getScenarioResult = useMemo(() => {
        return (scenarioId: number) => {
            if (!savedResults) return null;
            // Find results matching this scenario_id, sorted by date desc
            const matching = savedResults
                .filter(r => r.scenario_id === scenarioId)
                .sort((a, b) => new Date(b.analysis_date).getTime() - new Date(a.analysis_date).getTime());
            return matching.length > 0 ? matching[0] : null;
        };
    }, [savedResults]);

    // Toggle scenario selection
    const toggleScenario = (scenarioId: number) => {
        setSelectedScenarios(prev => {
            const next = new Set(prev);
            if (next.has(scenarioId)) {
                next.delete(scenarioId);
            } else {
                next.add(scenarioId);
            }
            return next;
        });
    };

    // Select all scenarios
    const selectAll = () => {
        setSelectedScenarios(new Set(scenarios?.map(s => s.id) || []));
    };

    // Deselect all scenarios
    const deselectAll = () => {
        setSelectedScenarios(new Set());
    };

    const handleRun = async () => {
        if (selectedScenarios.size === 0) {
            alert('Please select at least one scenario to run');
            return;
        }

        const selectedIds = Array.from(selectedScenarios);

        // Log the start
        addLog(`=== Analysis Run Started ===`, 'info');
        addLog(`Processing ${selectedScenarios.size} scenario(s)...`, 'info');
        addLog('', 'info');

        try {
            const result = await onRunAnalysis(selectedIds);

            // Process each scenario result and display engine logs
            if (result?.scenarios) {
                for (const scenarioResult of result.scenarios) {
                    addLog(`▸ ${scenarioResult.scenario_name} (${scenarioResult.cso_name})`, 'info');

                    // Display engine logs if available
                    if (scenarioResult.log && scenarioResult.log.length > 0) {
                        for (const logLine of scenarioResult.log) {
                            addLog(logLine, 'info');
                        }
                    }

                    if (scenarioResult.status === 'success') {
                        addLog(`  ✓ ${scenarioResult.spill_count} spills, ${scenarioResult.final_storage_m3} m³ storage`, 'success');
                    } else {
                        addLog(`  ✗ Error: ${scenarioResult.message}`, 'error');
                    }
                    addLog('', 'info');
                }
            }

            addLog('✓ Analysis completed successfully', 'success');
            addLog('  Navigate to the Results tab to view output.', 'info');
            addLog(`=== Analysis Run Complete ===`, 'info');
        } catch (error) {
            addLog('', 'info');
            addLog(`✗ Analysis failed: ${error instanceof Error ? error.message : String(error)}`, 'error');
            addLog(`=== Analysis Run Failed ===`, 'error');
        }
    };

    // Format timestamp for log
    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-32">
                <Loader2 className="animate-spin text-orange-500" size={24} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Pre-flight Checks */}
            <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Pre-flight Checks</h3>
                <div className="space-y-3">
                    {preflightChecks.map((check, idx) => (
                        <div key={idx} className="flex items-center gap-3">
                            {check.passed ? (
                                <CheckCircle size={20} className="text-green-500 flex-shrink-0" />
                            ) : check.critical ? (
                                <XCircle size={20} className="text-red-500 flex-shrink-0" />
                            ) : (
                                <AlertTriangle size={20} className="text-amber-500 flex-shrink-0" />
                            )}
                            <div className="flex-1">
                                <span className={check.passed ? 'text-gray-700' : check.critical ? 'text-red-700' : 'text-amber-700'}>
                                    {check.label}
                                </span>
                                {check.detail && (
                                    <span className="text-gray-400 text-sm ml-2">
                                        — {check.detail}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Scenario Queue */}
            {scenarios && scenarios.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Layers size={18} className="text-gray-400" />
                            Scenario Queue
                        </h3>
                        <div className="flex gap-2">
                            <button
                                onClick={selectAll}
                                className="text-sm text-orange-600 hover:text-orange-700"
                            >
                                Select All
                            </button>
                            <span className="text-gray-300">|</span>
                            <button
                                onClick={deselectAll}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                Clear
                            </button>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500 mb-4">
                        Select which scenarios to run. Each scenario combines a CSO asset with a configuration and intervention parameters.
                    </p>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                        {scenarios.map((scenario) => {
                            const result = getScenarioResult(scenario.id);
                            const hasBeenRun = !!result;

                            return (
                                <div
                                    key={scenario.id}
                                    onClick={() => toggleScenario(scenario.id)}
                                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition ${selectedScenarios.has(scenario.id)
                                        ? 'bg-orange-50 border border-orange-200'
                                        : hasBeenRun
                                            ? 'bg-green-50 border border-green-200 hover:border-green-300'
                                            : 'bg-gray-50 border border-gray-100 hover:border-gray-200'
                                        }`}
                                >
                                    {selectedScenarios.has(scenario.id) ? (
                                        <CheckSquare size={20} className="text-orange-600 flex-shrink-0" />
                                    ) : (
                                        <Square size={20} className={hasBeenRun ? 'text-green-500' : 'text-gray-400'} />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium text-gray-900 truncate">{scenario.scenario_name}</p>
                                            {hasBeenRun && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                                                    <CheckCircle size={10} className="mr-1" />
                                                    Run
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-gray-500 truncate">
                                            {getCSOName(scenario.cso_asset_id)} • {getConfigName(scenario.config_id)}
                                        </p>
                                        {hasBeenRun && result && (
                                            <p className="text-xs text-green-600 flex items-center gap-1 mt-0.5">
                                                <Clock size={10} />
                                                {new Date(result.analysis_date).toLocaleDateString()} —
                                                {result.final_storage_m3.toLocaleString()} m³, {result.spill_count} spills
                                            </p>
                                        )}
                                    </div>
                                    <div className="text-right text-xs text-gray-400 flex-shrink-0">
                                        <p>PFF: +{scenario.pff_increase} m³/s</p>
                                        {scenario.pump_rate > 0 && <p>Pump: {scenario.pump_rate} m³/s</p>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Run Button */}
            <div className="flex flex-col items-center py-6">
                <button
                    onClick={handleRun}
                    disabled={isRunning || !readyToRun}
                    className="bg-orange-600 text-white px-12 py-4 rounded-xl hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 font-semibold text-lg shadow-lg hover:shadow-xl"
                >
                    {isRunning ? (
                        <>
                            <Loader2 className="animate-spin" size={24} />
                            Running Analysis...
                        </>
                    ) : (
                        <>
                            <Play size={24} />
                            Run Analysis ({selectedScenarios.size} scenario{selectedScenarios.size !== 1 ? 's' : ''})
                        </>
                    )}
                </button>

                {!allChecksPassed && (
                    <p className="text-red-600 text-sm mt-4">
                        ❌ Complete all pre-flight checks before running analysis
                    </p>
                )}
                {allChecksPassed && selectedScenarios.size === 0 && (
                    <p className="text-amber-600 text-sm mt-4">
                        ⚠ Select at least one scenario from the queue above
                    </p>
                )}
            </div>

            {/* Analysis Log */}
            <div className="bg-gray-900 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                        <Terminal size={16} />
                        Analysis Log
                    </h3>
                    <button
                        onClick={clearLog}
                        className="text-gray-500 hover:text-gray-300 text-xs flex items-center gap-1"
                    >
                        <Trash2 size={12} />
                        Clear
                    </button>
                </div>
                <div className="font-mono text-xs h-40 overflow-y-auto space-y-1">
                    {analysisLog.length === 0 ? (
                        <p className="text-gray-600 italic">Ready to run analysis...</p>
                    ) : (
                        analysisLog.map((entry, idx) => (
                            <div key={idx} className={`${entry.type === 'success' ? 'text-green-400' :
                                entry.type === 'error' ? 'text-red-400' :
                                    entry.type === 'warning' ? 'text-amber-400' :
                                        'text-gray-400'
                                }`}>
                                <span className="text-gray-600">[{formatTime(entry.timestamp)}]</span> {entry.message}
                            </div>
                        ))
                    )}
                    <div ref={logEndRef} />
                </div>
            </div>
        </div>
    );
};

export default AnalysisTab;
