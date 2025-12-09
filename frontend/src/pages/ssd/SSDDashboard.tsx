import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    ArrowLeft, Upload, Container, MapPin, Building, Settings,
    Layers, Play, BarChart2, Loader2
} from 'lucide-react';
import { useSSDProject, useSSDScenarioAnalysis } from '../../api/hooks';
import DataImportTab from './DataImportTab';
import CSOAssetsTab from './CSOAssetsTab';
import AnalysisConfigTab from './AnalysisConfigTab';
import ScenariosTab from './ScenariosTab';
import AnalysisTab from './AnalysisTab';
import ResultsTab from './ResultsTab';

// Type definitions

interface SpillEvent {
    start_time: string;
    end_time: string;
    duration_hours: number;
    volume_m3: number;
    peak_flow_m3s: number;
    is_bathing_season: boolean;
}

interface SSDAnalysisResult {
    success: boolean;
    cso_name: string;
    converged: boolean;
    iterations: number;
    final_storage_m3: number;
    spill_count: number;
    bathing_spill_count: number;
    total_spill_volume_m3: number;
    bathing_spill_volume_m3: number;
    total_spill_duration_hours: number;
    spill_events: SpillEvent[];
    error?: string;
}

type TabId = 'data-import' | 'cso-assets' | 'catchments' | 'wwtw-assets' | 'analysis-configs' | 'analysis-scenarios' | 'analysis' | 'results';

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: 'data-import', label: 'Data Import', icon: Upload },
    { id: 'cso-assets', label: 'CSO Assets', icon: Container },
    { id: 'catchments', label: 'Catchments', icon: MapPin },
    { id: 'wwtw-assets', label: 'WwTW Assets', icon: Building },
    { id: 'analysis-configs', label: 'Analysis Configs', icon: Settings },
    { id: 'analysis-scenarios', label: 'Scenarios', icon: Layers },
    { id: 'analysis', label: 'Analysis', icon: Play },
    { id: 'results', label: 'Results', icon: BarChart2 },
];



export default function SSDDashboard() {
    const { projectId } = useParams();
    const numericProjectId = parseInt(projectId || '0', 10);

    // Data hooks
    const { data: project, isLoading: projectLoading } = useSSDProject(numericProjectId);
    const scenarioAnalysisMutation = useSSDScenarioAnalysis();

    // Tab state
    const [activeTab, setActiveTab] = useState<TabId>('data-import');

    // Results state
    const [analysisResult, setAnalysisResult] = useState<SSDAnalysisResult | null>(null);
    const [scenarioResults, setScenarioResults] = useState<any>(null);


    const handleRunAnalysis = async (scenarioIds: number[]) => {
        try {
            console.log('Starting analysis for scenarios:', scenarioIds);
            const result = await scenarioAnalysisMutation.mutateAsync({
                projectId: numericProjectId,
                scenarioIds
            });
            console.log('Analysis complete, result:', result);
            setScenarioResults(result);
            // Return result so AnalysisTab can display engine logs
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

                <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
                <p className="text-gray-500 mt-1">
                    {project.client} • {project.job_number}
                </p>
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

                {activeTab === 'cso-assets' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">CSO Assets</h2>
                        <p className="text-gray-500 mb-6">
                            Define Combined Sewer Overflow (CSO) configurations and link mappings.
                        </p>
                        <CSOAssetsTab projectId={numericProjectId} />
                    </div>
                )}

                {activeTab === 'catchments' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Catchments</h2>
                        <p className="text-gray-500 mb-6">
                            Define catchment areas and groupings for analysis.
                        </p>
                        <div className="text-center py-16 text-gray-400">
                            <MapPin size={48} className="mx-auto mb-4 opacity-50" />
                            <p>Coming Soon</p>
                            <p className="text-sm mt-2">Catchment management will be available in a future update.</p>
                        </div>
                    </div>
                )}

                {activeTab === 'wwtw-assets' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-2">WwTW Assets</h2>
                        <p className="text-gray-500 mb-6">
                            Define Wastewater Treatment Works configurations.
                        </p>
                        <div className="text-center py-16 text-gray-400">
                            <Building size={48} className="mx-auto mb-4 opacity-50" />
                            <p>Coming Soon</p>
                            <p className="text-sm mt-2">WwTW asset management will be available in a future update.</p>
                        </div>
                    </div>
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
                        <ResultsTab result={analysisResult} />
                    </div>
                )}
            </div>
        </div>
    );
}
