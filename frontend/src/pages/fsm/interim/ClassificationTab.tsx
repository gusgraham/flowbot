import React, { useState } from 'react';
import { useSignoffReviewStage, useReviewClassifications, useRunClassification, useOverrideClassification, useModelsStatus } from '../../../api/hooks';
import type { InterimReview, DailyClassification } from '../../../api/hooks';
import { useToast } from '../../../contexts/ToastContext';
import { CheckCircle2, AlertTriangle, Loader2, Tag, Zap, Play, Edit2, X, AlertCircle, TrendingUp } from 'lucide-react';
import FlowMonitorChart from './FlowMonitorChart';
import RainGaugeChart from './RainGaugeChart';
import PumpLoggerChart from './PumpLoggerChart';

interface ClassificationTabProps {
    review: InterimReview;
    username: string;
    onRefresh: () => void;
    startDate?: string;
    endDate?: string;
}

const classificationCodes: Record<string, string> = {
    'X': 'Not Working',
    'G': 'Dry Pipe',
    'L': 'Low Flow <10l/s',
    'P': 'Pluming',
    'U': 'Dislodged Sensor',
    'O': 'Taken Out',
    'V': 'Velocity Problem',
    'B': 'Blocked Filter RG',
    'T': 'Sediment',
    'K': 'Monitor Submerged',
    'H': 'Standing Water',
    'M': 'Monitor Changed',
    'D': 'Depth Problem',
    'R': 'Ragging',
    'S': 'Surcharged',
    'W': 'Working',
    'I': 'Installed'
};

const classificationOptions = Object.entries(classificationCodes).map(([code, desc]) => ({
    value: code,
    label: `${code} - ${desc}`
}));

const ClassificationTab: React.FC<ClassificationTabProps> = ({ review, username, onRefresh, startDate, endDate }) => {
    const [comment, setComment] = useState(review.classification_comment || '');
    const [editingId, setEditingId] = useState<number | null>(null);
    const [overrideClass, setOverrideClass] = useState('');
    const [overrideReason, setOverrideReason] = useState('');
    const [selectedVariable, setSelectedVariable] = useState<string>('All');
    const [hoveredDate, setHoveredDate] = useState<string | null>(null);

    React.useEffect(() => {
        // console.log('ClassTab Review:', review);
        // console.log('Dates:', review.start_date, review.end_date);
    }, [review]);

    const { mutate: signoff, isPending: isSigningOff } = useSignoffReviewStage();
    const { data: classifications, refetch: refetchClassifications, isLoading } = useReviewClassifications(review.id);
    const { mutate: runClassification, isPending: isRunning } = useRunClassification();
    const { mutate: overrideClassification, isPending: isOverriding } = useOverrideClassification();
    const { data: modelsStatus } = useModelsStatus();
    const { showToast } = useToast();

    const handleRunClassification = () => {
        runClassification(review.id, {
            onSuccess: (data: any) => {
                showToast(`Classification complete: ${data.results_count} days processed`, 'success');
                refetchClassifications();
            },
            onError: (err) => {
                showToast(`Classification failed: ${err.message}`, 'error');
            },
        });
    };

    const handleOverride = (classificationId: number) => {
        if (!overrideClass) {
            showToast('Please select a classification', 'error');
            return;
        }

        overrideClassification(
            { classificationId, manual_classification: overrideClass, override_reason: overrideReason },
            {
                onSuccess: () => {
                    showToast('Classification overridden', 'success');
                    setEditingId(null);
                    setOverrideClass('');
                    setOverrideReason('');
                    refetchClassifications();
                },
                onError: (err) => {
                    showToast(`Override failed: ${err.message}`, 'error');
                },
            }
        );
    };

    const handleSignoff = () => {
        signoff(
            { reviewId: review.id, stage: 'classification', comment, reviewer: username },
            {
                onSuccess: () => {
                    showToast('Classification review signed off', 'success');
                    onRefresh();
                },
                onError: (err) => {
                    showToast(`Sign-off failed: ${err.message}`, 'error');
                },
            }
        );
    };

    const isComplete = review.classification_complete;

    // Determine model type for this install
    const modelType = review.install_type === 'Flow Monitor' ? 'FM' :
        review.install_type === 'Rain Gauge' ? 'RG' : 'DM';
    const modelAvailable = modelsStatus?.[modelType] ?? false;

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return 'text-green-600';
        if (confidence >= 0.5) return 'text-amber-600';
        return 'text-red-600';
    };

    const getClassificationBadge = (classification: string) => {
        // Map codes to colors
        // Green: Working, Installed
        // Red: Not Working, Taken Out, Blocked
        // Amber: Problems (Ragging, Surcharged, etc.)
        // Gray: Dry, Off, etc.

        const greenCodes = ['W', 'I', 'Good'];
        const redCodes = ['X', 'O', 'B', 'Bad'];
        const amberCodes = ['L', 'P', 'U', 'V', 'T', 'K', 'H', 'M', 'D', 'R', 'S', 'Suspect'];

        if (greenCodes.includes(classification)) return 'bg-green-100 text-green-700';
        if (redCodes.includes(classification)) return 'bg-red-100 text-red-700';
        if (amberCodes.includes(classification)) return 'bg-amber-100 text-amber-700';

        return 'bg-gray-100 text-gray-500';
    };

    const getVariableOptions = () => {
        if (review.install_type === 'Flow Monitor') {
            return ['All', 'Flow', 'Depth', 'Velocity'];
        }
        if (review.install_type === 'Rain Gauge') {
            return ['All', 'Intensity', 'Cumulative'];
        }
        return [];
    };

    return (
        <div className="space-y-6">
            {/* Status Banner */}
            {isComplete ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle2 className="text-green-500" size={24} />
                    <div>
                        <p className="font-medium text-green-800">Classification Review Complete</p>
                        <p className="text-sm text-green-600">
                            Reviewed by {review.classification_reviewer} on{' '}
                            {review.classification_reviewed_at
                                ? new Date(review.classification_reviewed_at).toLocaleString()
                                : 'N/A'}
                        </p>
                    </div>
                </div>
            ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={24} />
                    <div>
                        <p className="font-medium text-amber-800">Pending Classification Review</p>
                        <p className="text-sm text-amber-600">
                            Run ML classification, review results, and make manual overrides as needed.
                        </p>
                    </div>
                </div>
            )}

            {/* Model Status */}
            {!modelAvailable && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
                    <AlertCircle className="text-red-500" size={24} />
                    <div>
                        <p className="font-medium text-red-800">ML Model Not Found</p>
                        <p className="text-sm text-red-600">
                            The {modelType} model is not available. Please add {modelType}_model.{modelType === 'FM' ? 'cbm' : 'pkl'} to
                            <code className="mx-1 bg-red-100 px-1 rounded">backend/resources/classifier/models/</code>
                        </p>
                    </div>
                </div>
            )}

            {/* Run Classification */}
            {!isComplete && modelAvailable && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <Zap size={20} className="text-purple-500" />
                                ML Classification
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">
                                Run the ML model to classify each day's data quality.
                            </p>
                        </div>
                        <button
                            onClick={handleRunClassification}
                            disabled={isRunning}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                            {isRunning ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                            Run Classification
                        </button>
                    </div>
                </div>
            )}

            {/* Data Visualization Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <TrendingUp size={20} className="text-blue-500" />
                        Data Visualization
                    </h3>

                    {getVariableOptions().length > 0 && (
                        <div className="flex items-center gap-2">
                            <label className="text-sm text-gray-600">Variable:</label>
                            <select
                                value={selectedVariable}
                                onChange={(e) => setSelectedVariable(e.target.value)}
                                className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {getVariableOptions().map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {review.install_type === 'Flow Monitor' && (
                    <FlowMonitorChart
                        installId={review.install_id}
                        startDate={startDate || review.start_date}
                        endDate={endDate || review.end_date}
                        visibleVariables={selectedVariable === 'All' ? undefined : [selectedVariable]}
                        highlightDate={hoveredDate}
                    />
                )}

                {review.install_type === 'Rain Gauge' && (
                    <RainGaugeChart
                        installId={review.install_id}
                        startDate={startDate || review.start_date}
                        endDate={endDate || review.end_date}
                        visibleVariables={selectedVariable === 'All' ? undefined : [selectedVariable]}
                        highlightDate={hoveredDate}
                    />
                )}

                {review.install_type === 'Pump Logger' && (
                    <PumpLoggerChart
                        installId={review.install_id}
                    />
                )}
            </div>

            {/* Classification Results */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Tag size={20} className="text-purple-500" />
                    Daily Classifications ({classifications?.length || 0} days)
                </h3>

                {isLoading ? (
                    <div className="text-center py-8">
                        <Loader2 size={32} className="animate-spin text-gray-400 mx-auto" />
                    </div>
                ) : classifications && classifications.length > 0 ? (
                    <div className="max-h-96 overflow-y-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 sticky top-0">
                                <tr>
                                    <th className="text-left p-2 font-medium text-gray-600">Date</th>
                                    <th className="text-left p-2 font-medium text-gray-600">ML Classification</th>
                                    <th className="text-left p-2 font-medium text-gray-600">Confidence</th>
                                    <th className="text-left p-2 font-medium text-gray-600">Override</th>
                                    {!isComplete && <th className="text-right p-2 font-medium text-gray-600">Actions</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {classifications.map((c: DailyClassification) => (
                                    <tr
                                        key={c.id}
                                        className="border-t border-gray-100 hover:bg-gray-50 transition-colors cursor-default"
                                        onMouseEnter={() => setHoveredDate(c.date)}
                                        onMouseLeave={() => setHoveredDate(null)}
                                    >
                                        <td className="p-2">{new Date(c.date).toLocaleDateString()}</td>
                                        <td className="p-2">
                                            <span className={`px-2 py-1 rounded-full text-xs ${getClassificationBadge(c.ml_classification)}`}>
                                                {c.ml_classification}
                                            </span>
                                        </td>
                                        <td className="p-2">
                                            <span className={`font-medium ${getConfidenceColor(c.ml_confidence)}`}>
                                                {(c.ml_confidence * 100).toFixed(1)}%
                                            </span>
                                        </td>
                                        <td className="p-2">
                                            {c.manual_classification ? (
                                                <div className="flex flex-col">
                                                    <span className={`px-2 py-1 rounded-full text-xs w-fit ${getClassificationBadge(c.manual_classification)}`}>
                                                        {c.manual_classification}
                                                    </span>
                                                    <span className="text-xs text-gray-500 mt-0.5">
                                                        {classificationCodes[c.manual_classification] || c.manual_classification}
                                                    </span>
                                                </div>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        {!isComplete && (
                                            <td className="p-2 text-right">
                                                {editingId === c.id ? (
                                                    <div className="flex items-center gap-2 justify-end">
                                                        <select
                                                            value={overrideClass}
                                                            onChange={(e) => setOverrideClass(e.target.value)}
                                                            className="border rounded px-2 py-1 text-xs max-w-[150px]"
                                                        >
                                                            <option value="">Select...</option>
                                                            {classificationOptions.map((opt) => (
                                                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                            ))}
                                                        </select>
                                                        <button
                                                            onClick={() => handleOverride(c.id)}
                                                            disabled={isOverriding}
                                                            className="text-green-600 hover:text-green-800"
                                                        >
                                                            {isOverriding ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                setEditingId(null);
                                                                setOverrideClass('');
                                                            }}
                                                            className="text-gray-400 hover:text-gray-600"
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <button
                                                        onClick={() => {
                                                            setEditingId(c.id);
                                                            setOverrideClass(c.manual_classification || '');
                                                        }}
                                                        className="text-gray-400 hover:text-purple-600"
                                                    >
                                                        <Edit2 size={14} />
                                                    </button>
                                                )}
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-400">
                        <Tag size={48} className="mx-auto mb-2 text-gray-300" />
                        <p>No classifications yet.</p>
                        <p className="text-sm">Click "Run Classification" to generate ML predictions.</p>
                    </div>
                )}
            </div>

            {/* Comments & Sign-off */}
            {!isComplete && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Review Sign-off
                    </h3>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Comments (optional)
                        </label>
                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Add any comments about the classification review..."
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <button
                        onClick={handleSignoff}
                        disabled={isSigningOff}
                        className="w-full px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isSigningOff ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <CheckCircle2 size={18} />
                        )}
                        Sign Off Classification Review
                    </button>
                </div>
            )}

            {/* Show comment if already complete */}
            {isComplete && review.classification_comment && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Review Comments</h3>
                    <p className="text-gray-600">{review.classification_comment}</p>
                </div>
            )}
        </div>
    );
};

export default ClassificationTab;
