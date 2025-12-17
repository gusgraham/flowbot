import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Pencil, Calendar, MapPin, Grid3X3, Sun } from 'lucide-react';
import { useVerificationProject } from '../../api/hooks';
import EventsTab from './verification/EventsTab';
import MonitorsTab from './verification/MonitorsTab';
import ReviewTab from './verification/ReviewTab';
import DryDayTab from './verification/DryDayTab';

// Type definitions
type TabId = 'events' | 'monitors' | 'drydays' | 'review';

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: 'events', label: 'Events & Import', icon: Calendar },
    { id: 'monitors', label: 'Monitors', icon: MapPin },
    { id: 'drydays', label: 'Dry Day Analysis', icon: Sun },
    { id: 'review', label: 'Verification Review', icon: Grid3X3 },
];

const VerificationDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const numericProjectId = parseInt(projectId || '0', 10);

    const { data: project, isLoading } = useVerificationProject(numericProjectId);

    // Tab state
    const [activeTab, setActiveTab] = useState<TabId>('events');

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-green-500" size={32} />
            </div>
        );
    }

    if (!project) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">Project not found</p>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <Link to="/verification" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Projects
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
                        <p className="text-gray-500 mt-1">
                            {project.client} • {project.job_number}
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/verification', { state: { editProjectId: numericProjectId } })}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <Pencil size={16} />
                        Edit Project
                    </button>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-1 overflow-x-auto">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap transition
                                    ${isActive
                                        ? 'border-green-500 text-green-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }
                                `}
                            >
                                <Icon size={18} />
                                {tab.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
                {activeTab === 'events' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Events & Trace Import</h2>
                        <p className="text-gray-500 mb-6">
                            Define verification events (storms, DWF) and import ICM trace files for comparison.
                        </p>
                        <EventsTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'monitors' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Flow Monitors</h2>
                        <p className="text-gray-500 mb-6">
                            Configure flow monitors for verification. Set critical/surcharged flags for tolerance adjustments.
                        </p>
                        <MonitorsTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'drydays' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Dry Day Analysis</h2>
                        <p className="text-gray-500 mb-6">
                            Import full-period observed data, detect dry days, and analyze 24-hour flow patterns.
                        </p>
                        <DryDayTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'review' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Verification Review</h2>
                        <p className="text-gray-500 mb-6">
                            Review verification results, detailed charts, and scores for each monitor.
                        </p>
                        <ReviewTab projectId={numericProjectId} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default VerificationDashboard;
