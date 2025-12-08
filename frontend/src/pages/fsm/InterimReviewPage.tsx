import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useInterim, useInterimReviews, useInterimReview } from '../../api/hooks';
import type { InterimReview } from '../../api/hooks';
import {
    ArrowLeft, Loader2, Calendar, CheckCircle2, Circle, AlertCircle,
    Database, Tag, CloudRain, LineChart
} from 'lucide-react';
import DataImportTab from './interim/DataImportTab';
import ClassificationTab from './interim/ClassificationTab';
import ProcessedReviewTab from './interim/ProcessedReviewTab';

type ReviewStage = 'data_import' | 'classification' | 'review';

const InterimReviewPage: React.FC = () => {
    const { interimId } = useParams<{ interimId: string }>();
    const id = parseInt(interimId || '0');

    const { data: interim, isLoading: interimLoading } = useInterim(id);
    const { data: reviews, isLoading: reviewsLoading, refetch: refetchReviews } = useInterimReviews(id);

    const [activeTab, setActiveTab] = useState<ReviewStage>('data_import');
    const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);

    // Get the currently logged-in user (from localStorage for now)
    const username = localStorage.getItem('username') || 'Unknown';

    // Select first review by default when reviews load
    useEffect(() => {
        if (reviews && reviews.length > 0 && !selectedReviewId) {
            setSelectedReviewId(reviews[0].id);
        }
    }, [reviews, selectedReviewId]);

    // Fetch selected review details
    const { data: selectedReview, refetch: refetchSelectedReview } = useInterimReview(selectedReviewId || 0);

    const handleRefresh = () => {
        refetchReviews();
        refetchSelectedReview();
    };

    if (interimLoading || reviewsLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (!interim) {
        return <div className="p-8 text-center text-gray-500">Interim not found</div>;
    }

    const totalReviews = reviews?.length || 0;
    const completedReviews = reviews?.filter(r => r.review_complete).length || 0;
    const progressPct = totalReviews > 0 ? Math.round((completedReviews / totalReviews) * 100) : 0;

    // Per-install review tabs (reduced to 3 stages - Events moved to interim level)
    const tabs: { key: ReviewStage; label: string; icon: React.ReactNode }[] = [
        { key: 'data_import', label: '1. Data Import', icon: <Database size={16} /> },
        { key: 'classification', label: '2. Classification', icon: <Tag size={16} /> },
        { key: 'review', label: '3. Review', icon: <LineChart size={16} /> },
    ];

    const getStageStatus = (review: InterimReview, stage: ReviewStage): 'complete' | 'incomplete' | 'warning' => {
        switch (stage) {
            case 'data_import':
                return review.data_import_acknowledged ? 'complete' : 'incomplete';
            case 'classification':
                return review.classification_complete ? 'complete' : 'incomplete';
            case 'review':
                return review.review_complete ? 'complete' : 'incomplete';
            default:
                return 'incomplete';
        }
    };

    const getStatusIcon = (status: 'complete' | 'incomplete' | 'warning') => {
        switch (status) {
            case 'complete':
                return <CheckCircle2 size={16} className="text-green-500" />;
            case 'warning':
                return <AlertCircle size={16} className="text-amber-500" />;
            default:
                return <Circle size={16} className="text-gray-300" />;
        }
    };

    const renderTabContent = () => {
        if (!selectedReview) {
            return (
                <div className="text-center text-gray-400 py-8">
                    Select an install from the list to start reviewing.
                </div>
            );
        }

        switch (activeTab) {
            case 'data_import':
                return <DataImportTab review={selectedReview} username={username} onRefresh={handleRefresh} />;
            case 'classification':
                return <ClassificationTab review={selectedReview} username={username} onRefresh={handleRefresh} />;
            case 'review':
                return <ProcessedReviewTab
                    review={selectedReview}
                    username={username}
                    onRefresh={handleRefresh}
                    startDate={interim?.start_date}
                    endDate={interim?.end_date}
                />; default:
                return null;
        }
    };

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <Link to={`/fsm/${interim.project_id}`} className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Project
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                            <Calendar size={24} className="text-purple-500" />
                            Interim Review
                        </h1>
                        <p className="text-gray-500 mt-1">
                            {new Date(interim.start_date).toLocaleDateString()} - {new Date(interim.end_date).toLocaleDateString()}
                        </p>
                    </div>

                    <div className="text-right">
                        <div className="text-sm text-gray-500 mb-1">Progress</div>
                        <div className="flex items-center gap-3">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full ${progressPct === 100 ? 'bg-green-500' : 'bg-purple-500'}`}
                                    style={{ width: `${progressPct}%` }}
                                />
                            </div>
                            <span className="font-medium">{completedReviews}/{totalReviews}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Install List (Left Sidebar) */}
                <div className="col-span-3">
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div className="p-4 bg-gray-50 border-b border-gray-200">
                            <h3 className="font-semibold text-gray-900">Installs ({totalReviews})</h3>
                        </div>
                        <div className="max-h-[calc(100vh-300px)] overflow-y-auto">
                            {reviews?.map((review) => {
                                const allComplete = review.data_import_acknowledged &&
                                    review.classification_complete &&
                                    review.review_complete;

                                return (
                                    <div
                                        key={review.id}
                                        onClick={() => setSelectedReviewId(review.id)}
                                        className={`p-3 border-b border-gray-100 cursor-pointer transition-colors ${selectedReviewId === review.id
                                            ? 'bg-purple-50 border-l-4 border-l-purple-500'
                                            : 'hover:bg-gray-50'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="font-medium text-gray-900 text-sm">
                                                    Install {review.install_id}
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    {review.install_type}
                                                </p>
                                            </div>
                                            {allComplete ? (
                                                <CheckCircle2 size={18} className="text-green-500" />
                                            ) : (
                                                <div className="flex gap-1">
                                                    <span className={`w-2 h-2 rounded-full ${review.data_import_acknowledged ? 'bg-green-500' : 'bg-gray-300'}`} />
                                                    <span className={`w-2 h-2 rounded-full ${review.classification_complete ? 'bg-green-500' : 'bg-gray-300'}`} />
                                                    <span className={`w-2 h-2 rounded-full ${review.review_complete ? 'bg-green-500' : 'bg-gray-300'}`} />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {(!reviews || reviews.length === 0) && (
                                <p className="text-center text-gray-400 py-8 text-sm">
                                    No reviews found
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Main Content (Right) */}
                <div className="col-span-9">
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        {/* Tabs */}
                        <div className="flex border-b border-gray-200">
                            {tabs.map((tab) => {
                                const tabStatus = selectedReview ? getStageStatus(selectedReview, tab.key) : 'incomplete';
                                return (
                                    <button
                                        key={tab.key}
                                        onClick={() => setActiveTab(tab.key)}
                                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === tab.key
                                            ? 'bg-purple-50 text-purple-700 border-b-2 border-purple-500'
                                            : 'text-gray-500 hover:bg-gray-50'
                                            }`}
                                    >
                                        {getStatusIcon(tabStatus)}
                                        {tab.icon}
                                        <span className="hidden lg:inline">{tab.label}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Tab Content */}
                        <div className="p-6">
                            {renderTabContent()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InterimReviewPage;
