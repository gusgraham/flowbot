import React, { useState } from 'react';
import { useSignoffReviewStage, useReviewAnnotations, useCreateAnnotation, useDeleteAnnotation } from '../../../api/hooks';
import type { InterimReview, ReviewAnnotation } from '../../../api/hooks';
import { useToast } from '../../../contexts/ToastContext';
import { CheckCircle2, AlertTriangle, Loader2, LineChart, Plus, Trash2, X } from 'lucide-react';
import FlowMonitorChart from './FlowMonitorChart';
import RainGaugeChart from './RainGaugeChart';
import PumpLoggerChart from './PumpLoggerChart';

interface ProcessedReviewTabProps {
    review: InterimReview;
    username: string;
    onRefresh: () => void;
    startDate?: string;
    endDate?: string;
    pipeHeight?: number;
}

const ProcessedReviewTab: React.FC<ProcessedReviewTabProps> = ({ review, username, onRefresh, startDate, endDate, pipeHeight }) => {
    const [comment, setComment] = useState(review.review_comment || '');
    const [showAddAnnotation, setShowAddAnnotation] = useState(false);
    const [newAnnotation, setNewAnnotation] = useState({
        variable: 'Depth',
        start_time: '',
        end_time: '',
        issue_type: 'anomaly',
        description: '',
    });

    const { mutate: signoff, isPending: isSigningOff } = useSignoffReviewStage();
    const { data: annotations, refetch: refetchAnnotations } = useReviewAnnotations(review.id);
    const { mutate: createAnnotation, isPending: isCreating } = useCreateAnnotation();
    const { mutate: deleteAnnotation } = useDeleteAnnotation();
    const { showToast } = useToast();

    const handleSignoff = () => {
        signoff(
            { reviewId: review.id, stage: 'review', comment, reviewer: username },
            {
                onSuccess: () => {
                    showToast('Processed data review signed off', 'success');
                    onRefresh();
                },
                onError: (err) => {
                    showToast(`Sign-off failed: ${err.message}`, 'error');
                },
            }
        );
    };

    const handleAddAnnotation = () => {
        if (!newAnnotation.start_time || !newAnnotation.end_time) {
            showToast('Please select start and end times', 'error');
            return;
        }

        createAnnotation(
            {
                reviewId: review.id,
                variable: newAnnotation.variable,
                start_time: new Date(newAnnotation.start_time).toISOString(),
                end_time: new Date(newAnnotation.end_time).toISOString(),
                issue_type: newAnnotation.issue_type,
                description: newAnnotation.description,
            },
            {
                onSuccess: () => {
                    showToast('Annotation added', 'success');
                    setShowAddAnnotation(false);
                    setNewAnnotation({
                        variable: 'Depth',
                        start_time: '',
                        end_time: '',
                        issue_type: 'anomaly',
                        description: '',
                    });
                    refetchAnnotations();
                },
                onError: (err) => {
                    showToast(`Failed to add annotation: ${err.message}`, 'error');
                },
            }
        );
    };

    const handleDeleteAnnotation = (annotationId: number) => {
        deleteAnnotation(annotationId, {
            onSuccess: () => {
                showToast('Annotation deleted', 'success');
                refetchAnnotations();
            },
            onError: (err) => {
                showToast(`Failed to delete: ${err.message}`, 'error');
            },
        });
    };

    const isComplete = review.review_complete;

    const issueTypeColors: Record<string, string> = {
        anomaly: 'bg-red-100 text-red-700',
        suspect: 'bg-amber-100 text-amber-700',
        gap: 'bg-gray-100 text-gray-700',
        calibration: 'bg-blue-100 text-blue-700',
        other: 'bg-purple-100 text-purple-700',
    };

    const variableOptions = ['Depth', 'Velocity', 'Flow', 'Rain', 'Pump_State'];
    const issueTypeOptions = [
        { value: 'anomaly', label: 'Anomaly' },
        { value: 'suspect', label: 'Suspect' },
        { value: 'gap', label: 'Gap' },
        { value: 'calibration', label: 'Calibration' },
        { value: 'other', label: 'Other' },
    ];

    return (
        <div className="space-y-6">
            {/* Status Banner */}
            {isComplete ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle2 className="text-green-500" size={24} />
                    <div>
                        <p className="font-medium text-green-800">Processed Data Review Complete</p>
                        <p className="text-sm text-green-600">
                            Reviewed by {review.review_reviewer} on{' '}
                            {review.review_reviewed_at
                                ? new Date(review.review_reviewed_at).toLocaleString()
                                : 'N/A'}
                        </p>
                    </div>
                </div>
            ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={24} />
                    <div>
                        <p className="font-medium text-amber-800">Pending Processed Data Review</p>
                        <p className="text-sm text-amber-600">
                            Review the processed data charts and add annotations for any issues.
                        </p>
                    </div>
                </div>
            )}

            {/* Monitor-Specific Charts */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <LineChart size={20} className="text-green-500" />
                    Processed Data Charts
                </h3>

                {review.install_type === 'Flow Monitor' && (
                    <FlowMonitorChart
                        installId={review.install_id}
                        startDate={startDate}
                        endDate={endDate}
                        pipeHeight={pipeHeight}
                    />
                )}

                {review.install_type === 'Rain Gauge' && (
                    <RainGaugeChart
                        installId={review.install_id}
                        startDate={startDate}
                        endDate={endDate}
                    />
                )}

                {(review.install_type === 'Pump Logger' || review.install_type === 'Pump Station') && (
                    <PumpLoggerChart
                        installId={review.install_id}
                        startDate={startDate}
                        endDate={endDate}
                    />
                )}

                {!['Flow Monitor', 'Rain Gauge', 'Pump Logger', 'Pump Station'].includes(review.install_type) && (
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                        <LineChart size={48} className="text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">No specific chart available for {review.install_type}</p>
                    </div>
                )}
            </div>

            {/* Annotations */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Annotations ({annotations?.length || 0})
                    </h3>
                    {!isComplete && (
                        <button
                            onClick={() => setShowAddAnnotation(true)}
                            className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                        >
                            <Plus size={16} />
                            Add Annotation
                        </button>
                    )}
                </div>

                {/* Add Annotation Form */}
                {showAddAnnotation && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <div className="flex justify-between items-center mb-3">
                            <h4 className="font-medium text-blue-800">New Annotation</h4>
                            <button onClick={() => setShowAddAnnotation(false)} className="text-blue-600 hover:text-blue-800">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-3">
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Variable</label>
                                <select
                                    value={newAnnotation.variable}
                                    onChange={(e) => setNewAnnotation({ ...newAnnotation, variable: e.target.value })}
                                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {variableOptions.map((v) => (
                                        <option key={v} value={v}>{v}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Issue Type</label>
                                <select
                                    value={newAnnotation.issue_type}
                                    onChange={(e) => setNewAnnotation({ ...newAnnotation, issue_type: e.target.value })}
                                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {issueTypeOptions.map((opt) => (
                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-3">
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">Start Time</label>
                                <input
                                    type="datetime-local"
                                    value={newAnnotation.start_time}
                                    onChange={(e) => setNewAnnotation({ ...newAnnotation, start_time: e.target.value })}
                                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-600 mb-1">End Time</label>
                                <input
                                    type="datetime-local"
                                    value={newAnnotation.end_time}
                                    onChange={(e) => setNewAnnotation({ ...newAnnotation, end_time: e.target.value })}
                                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        <div className="mb-3">
                            <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                            <textarea
                                value={newAnnotation.description}
                                onChange={(e) => setNewAnnotation({ ...newAnnotation, description: e.target.value })}
                                placeholder="Describe the issue..."
                                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm h-16 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <button
                            onClick={handleAddAnnotation}
                            disabled={isCreating}
                            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isCreating && <Loader2 size={16} className="animate-spin" />}
                            Save Annotation
                        </button>
                    </div>
                )}

                {/* Annotation List */}
                {annotations && annotations.length > 0 ? (
                    <div className="space-y-2">
                        {annotations.map((annotation: ReviewAnnotation) => (
                            <div
                                key={annotation.id}
                                className="flex justify-between items-start bg-gray-50 rounded-lg p-3"
                            >
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-medium text-gray-900">{annotation.variable}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${issueTypeColors[annotation.issue_type] || issueTypeColors.other}`}>
                                            {annotation.issue_type}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-500">
                                        {new Date(annotation.start_time).toLocaleString()} → {new Date(annotation.end_time).toLocaleString()}
                                    </p>
                                    {annotation.description && (
                                        <p className="text-sm text-gray-600 mt-1">{annotation.description}</p>
                                    )}
                                    <p className="text-xs text-gray-400 mt-1">
                                        Added by {annotation.created_by || 'Unknown'} on {new Date(annotation.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                                {!isComplete && (
                                    <button
                                        onClick={() => handleDeleteAnnotation(annotation.id)}
                                        className="text-gray-400 hover:text-red-500 p-1"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-center text-gray-400 py-4">
                        No annotations yet. Add annotations to note any data issues.
                    </p>
                )}
            </div>

            {/* Comments & Sign-off */}
            {!isComplete && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Final Review Sign-off
                    </h3>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Review Comments (optional)
                        </label>
                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Add any final comments about the processed data review..."
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
                        Complete Review
                    </button>
                </div>
            )}

            {/* Show comment if already complete */}
            {isComplete && review.review_comment && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Review Comments</h3>
                    <p className="text-gray-600">{review.review_comment}</p>
                </div>
            )}
        </div>
    );
};

export default ProcessedReviewTab;
