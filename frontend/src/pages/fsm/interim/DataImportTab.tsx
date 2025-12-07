import React, { useState } from 'react';
import { useSignoffReviewStage, useCalculateCoverage } from '../../../api/hooks';
import type { InterimReview } from '../../../api/hooks';
import { useToast } from '../../../contexts/ToastContext';
import { CheckCircle2, AlertTriangle, Loader2, Database, Clock, RefreshCw } from 'lucide-react';

interface DataImportTabProps {
    review: InterimReview;
    username: string;
    onRefresh: () => void;
}

const DataImportTab: React.FC<DataImportTabProps> = ({ review, username, onRefresh }) => {
    const [notes, setNotes] = useState(review.data_import_notes || '');
    const { mutate: signoff, isPending } = useSignoffReviewStage();
    const { mutate: calculateCoverage, isPending: isCalculating } = useCalculateCoverage();
    const { showToast } = useToast();

    const coveragePct = review.data_coverage_pct ?? 0;
    const gaps = review.gaps_json ? JSON.parse(review.gaps_json) : [];

    const handleSignoff = () => {
        signoff(
            { reviewId: review.id, stage: 'data_import', comment: notes, reviewer: username },
            {
                onSuccess: () => {
                    showToast('Data import stage signed off', 'success');
                    onRefresh();
                },
                onError: (err) => {
                    showToast(`Sign-off failed: ${err.message}`, 'error');
                },
            }
        );
    };

    const handleCalculateCoverage = () => {
        calculateCoverage(review.id, {
            onSuccess: (result: any) => {
                showToast(`Coverage calculated: ${result.coverage_pct?.toFixed(1)}%`, 'success');
                onRefresh();
            },
            onError: (err) => {
                showToast(`Coverage calculation failed: ${err.message}`, 'error');
            },
        });
    };

    const isComplete = review.data_import_acknowledged;

    return (
        <div className="space-y-6">
            {/* Status Banner */}
            {isComplete ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle2 className="text-green-500" size={24} />
                    <div>
                        <p className="font-medium text-green-800">Data Import Acknowledged</p>
                        <p className="text-sm text-green-600">
                            Reviewed by {review.data_import_reviewer} on{' '}
                            {review.data_import_reviewed_at
                                ? new Date(review.data_import_reviewed_at).toLocaleString()
                                : 'N/A'}
                        </p>
                    </div>
                </div>
            ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={24} />
                    <div>
                        <p className="font-medium text-amber-800">Pending Review</p>
                        <p className="text-sm text-amber-600">
                            Please verify data coverage and acknowledge any gaps.
                        </p>
                    </div>
                </div>
            )}

            {/* Coverage Metrics */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <Database size={20} className="text-blue-500" />
                        Data Coverage
                    </h3>
                    <button
                        onClick={handleCalculateCoverage}
                        disabled={isCalculating}
                        className="flex items-center gap-2 text-sm bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg hover:bg-blue-200 disabled:opacity-50"
                    >
                        {isCalculating ? (
                            <Loader2 size={14} className="animate-spin" />
                        ) : (
                            <RefreshCw size={14} />
                        )}
                        Calculate Coverage
                    </button>
                </div>

                <div className="grid grid-cols-2 gap-6">
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Coverage Percentage</p>
                        <div className="flex items-center gap-3">
                            <div className="flex-1 bg-gray-200 rounded-full h-4">
                                <div
                                    className={`h-4 rounded-full ${coveragePct >= 95 ? 'bg-green-500' :
                                        coveragePct >= 80 ? 'bg-amber-500' : 'bg-red-500'
                                        }`}
                                    style={{ width: `${coveragePct}%` }}
                                />
                            </div>
                            <span className="font-bold text-lg">{coveragePct.toFixed(1)}%</span>
                        </div>
                    </div>

                    <div>
                        <p className="text-sm text-gray-500 mb-1">Number of Gaps</p>
                        <p className="text-2xl font-bold text-gray-900">{gaps.length}</p>
                    </div>
                </div>
            </div>

            {/* Gaps List */}
            {gaps.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Clock size={20} className="text-amber-500" />
                        Data Gaps
                    </h3>

                    <div className="space-y-2 max-h-48 overflow-y-auto">
                        {gaps.map((gap: { start: string; end: string; duration_hours: number }, index: number) => (
                            <div
                                key={index}
                                className="flex justify-between items-center bg-gray-50 rounded px-4 py-2 text-sm"
                            >
                                <span>
                                    {new Date(gap.start).toLocaleString()} → {new Date(gap.end).toLocaleString()}
                                </span>
                                <span className="text-gray-500">
                                    {gap.duration_hours?.toFixed(1) || 'N/A'} hours
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Notes & Sign-off */}
            {!isComplete && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Acknowledgement
                    </h3>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Notes (optional)
                        </label>
                        <textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            placeholder="Add any notes about data coverage, missing data reasons, etc."
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
                        Acknowledge Data Import
                    </button>
                </div>
            )}

            {/* Show notes if already complete */}
            {isComplete && review.data_import_notes && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Notes</h3>
                    <p className="text-gray-600">{review.data_import_notes}</p>
                </div>
            )}
        </div>
    );
};

export default DataImportTab;
