import React, { useState } from 'react';
import { useSignoffReviewStage } from '../../../api/hooks';
import type { InterimReview } from '../../../api/hooks';
import { useToast } from '../../../contexts/ToastContext';
import { CheckCircle2, AlertTriangle, Loader2, CloudRain, Zap } from 'lucide-react';

interface EventsTabProps {
    review: InterimReview;
    username: string;
    onRefresh: () => void;
}

const EventsTab: React.FC<EventsTabProps> = ({ review, username, onRefresh }) => {
    const [comment, setComment] = useState(review.events_comment || '');
    const { mutate: signoff, isPending } = useSignoffReviewStage();
    const { showToast } = useToast();

    const handleSignoff = () => {
        signoff(
            { reviewId: review.id, stage: 'events', comment, reviewer: username },
            {
                onSuccess: () => {
                    showToast('Events review signed off', 'success');
                    onRefresh();
                },
                onError: (err) => {
                    showToast(`Sign-off failed: ${err.message}`, 'error');
                },
            }
        );
    };

    const isComplete = review.events_complete;

    return (
        <div className="space-y-6">
            {/* Status Banner */}
            {isComplete ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle2 className="text-green-500" size={24} />
                    <div>
                        <p className="font-medium text-green-800">Events Review Complete</p>
                        <p className="text-sm text-green-600">
                            Reviewed by {review.events_reviewer} on{' '}
                            {review.events_reviewed_at
                                ? new Date(review.events_reviewed_at).toLocaleString()
                                : 'N/A'}
                        </p>
                    </div>
                </div>
            ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={24} />
                    <div>
                        <p className="font-medium text-amber-800">Pending Events Review</p>
                        <p className="text-sm text-amber-600">
                            Verify detected rainfall events and confirm/reject as needed.
                        </p>
                    </div>
                </div>
            )}

            {/* Events Info */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <CloudRain size={20} className="text-cyan-500" />
                    Rainfall Event Detection
                </h3>

                <div className="bg-gray-50 rounded-lg p-8 text-center">
                    <Zap size={48} className="text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 mb-2">
                        Automated event detection will be integrated in a future phase.
                    </p>
                    <p className="text-sm text-gray-400">
                        This will include:
                    </p>
                    <ul className="text-sm text-gray-400 mt-2 space-y-1">
                        <li>• Automatic rainfall event detection (reusing FSA logic)</li>
                        <li>• Event list with start/end times and totals</li>
                        <li>• Confirm/reject/edit detected events</li>
                        <li>• Link events to the Event table</li>
                    </ul>
                </div>
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
                            placeholder="Add any comments about the events review..."
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <button
                        onClick={handleSignoff}
                        disabled={isPending}
                        className="w-full px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isPending ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <CheckCircle2 size={18} />
                        )}
                        Sign Off Events Review
                    </button>
                </div>
            )}

            {/* Show comment if already complete */}
            {isComplete && review.events_comment && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Review Comments</h3>
                    <p className="text-gray-600">{review.events_comment}</p>
                </div>
            )}
        </div>
    );
};

export default EventsTab;
