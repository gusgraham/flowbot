import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, Upload, Package, Settings,
    Layers, Play, BarChart2, Loader2, Pencil
} from 'lucide-react';
import { useSSDProject, useSSDScenarioAnalysis } from '../../api/hooks';
import DataImportTab from './DataImportTab';
import AssetsTab from './AssetsTab';
import AnalysisConfigTab from './AnalysisConfigTab';
import ScenariosTab from './ScenariosTab';
import AnalysisTab from './AnalysisTab';
import ResultsTab from './ResultsTab';

// Type definitions

type TabId = 'data-import' | 'assets' | 'analysis-configs' | 'analysis-scenarios' | 'analysis' | 'results';

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: 'data-import', label: 'Data Import', icon: Upload },
    { id: 'assets', label: 'Assets', icon: Package },
    { id: 'analysis-configs', label: 'Analysis Configs', icon: Settings },
    { id: 'analysis-scenarios', label: 'Scenarios', icon: Layers },
    { id: 'analysis', label: 'Analysis', icon: Play },
    { id: 'results', label: 'Results', icon: BarChart2 },
];



export default function SSDDashboard() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const numericProjectId = parseInt(projectId || '0', 10);

    // Data hooks
    const { data: project, isLoading: projectLoading } = useSSDProject(numericProjectId);
    const scenarioAnalysisMutation = useSSDScenarioAnalysis();

    // Tab state
    const [activeTab, setActiveTab] = useState<TabId>('data-import');

    // Results state - now stored in database, not local state


    const handleRunAnalysis = async (scenarioIds: number[]) => {
        try {
            //console.log('Starting analysis for scenarios:', scenarioIds);
            const result = await scenarioAnalysisMutation.mutateAsync({
                projectId: numericProjectId,
                scenarioIds
            });
            //console.log('Analysis complete, result:', result);
            // Results are auto-saved to database by backend
            return result;
        } catch (error) {
            console.error('Analysis failed:', error);
            throw error; // Re-throw so AnalysisTab can log it
        }
    };

    if (projectLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-orange-500" size={32} />
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
                <Link to="/ssd" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
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
                        onClick={() => navigate('/ssd', { state: { editProjectId: numericProjectId } })}
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
                                        ? 'border-orange-500 text-orange-600'
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
                {activeTab === 'data-import' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Data Import</h2>
                        <p className="text-gray-500 mb-6">
                            Upload InfoWorks ICM time-series exports (CSV format) for analysis.
                        </p>
                        <DataImportTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'assets' && (
                    <AssetsTab projectId={numericProjectId} />
                )}

                {activeTab === 'analysis-configs' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Analysis Configurations</h2>
                        <p className="text-gray-500 mb-6">
                            Define reusable analysis settings for CSO assessments.
                        </p>
                        <AnalysisConfigTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'analysis-scenarios' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Analysis Scenarios</h2>
                        <p className="text-gray-500 mb-6">
                            Define what-if scenarios by combining CSO assets with configurations and interventions.
                        </p>
                        <ScenariosTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'analysis' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Run Analysis</h2>
                        <p className="text-gray-500 mb-6">
                            Review pre-flight checks and execute storage analysis for selected scenarios.
                        </p>
                        <AnalysisTab
                            projectId={numericProjectId}
                            isRunning={scenarioAnalysisMutation.isPending}
                            onRunAnalysis={handleRunAnalysis}
                        />
                    </div>
                )}

                {activeTab === 'results' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Analysis Results</h2>
                        <p className="text-gray-500 mb-6">
                            View storage requirements, spill events, and analysis outputs.
                        </p>
                        <ResultsTab projectId={numericProjectId} />
                    </div>
                )}
            </div>
        </div>
    );
}
