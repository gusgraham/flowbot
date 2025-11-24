import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMonitor, useInstalls, useVisits } from '../../api/hooks';
import { ArrowLeft, Calendar, User, Ruler, FileText, Activity, Loader2 } from 'lucide-react';

const VisitList = ({ installId }: { installId: number }) => {
    const { data: visits, isLoading } = useVisits(installId);

    if (isLoading) return <div className="animate-pulse h-10 bg-gray-50 rounded"></div>;

    return (
        <div className="mt-4 space-y-2">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Visits</h4>
            {visits?.map((visit) => (
                <div key={visit.id} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded border border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1 text-gray-600">
                            <Calendar size={14} />
                            {new Date(visit.date).toLocaleDateString()}
                        </div>
                        <div className="flex items-center gap-1 text-gray-500">
                            <User size={14} />
                            {visit.crew}
                        </div>
                    </div>
                    {visit.stage_depth && (
                        <div className="flex items-center gap-1 text-blue-600 font-medium">
                            <Ruler size={14} />
                            {visit.stage_depth}m
                        </div>
                    )}
                </div>
            ))}
            {visits?.length === 0 && <p className="text-xs text-gray-400">No visits recorded.</p>}
        </div>
    );
};

const MonitorDetail: React.FC = () => {
    const { monitorId } = useParams<{ monitorId: string }>();
    const id = parseInt(monitorId || '0');

    const { data: monitor, isLoading: monitorLoading } = useMonitor(id);
    const { data: installs, isLoading: installsLoading } = useInstalls(id);

    if (monitorLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (!monitor) return <div>Monitor not found</div>;

    return (
        <div className="max-w-5xl mx-auto">
            <div className="mb-8">
                <Link to={`/fsm`} className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                            {monitor.name}
                            <span className="text-sm font-normal px-2 py-1 bg-gray-100 rounded-md text-gray-600">
                                {monitor.type}
                            </span>
                        </h1>
                        <p className="text-gray-500 mt-1">Status: {monitor.status}</p>
                    </div>

                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 flex items-center gap-2">
                            <FileText size={18} />
                            Interim Report
                        </button>
                        <button className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 flex items-center gap-2">
                            <Activity size={18} />
                            View Data
                        </button>
                    </div>
                </div>
            </div>

            <div className="space-y-8">
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <h2 className="text-xl font-bold text-gray-900 mb-6">Installation History</h2>

                    <div className="space-y-8">
                        {installs?.map((install) => (
                            <div key={install.id} className="relative pl-8 border-l-2 border-gray-200 last:border-0">
                                <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-4 border-white shadow-sm"></div>

                                <div className="mb-4">
                                    <h3 className="text-lg font-semibold text-gray-900">
                                        Installed on {new Date(install.install_date).toLocaleDateString()}
                                    </h3>
                                    {install.removal_date && (
                                        <p className="text-sm text-gray-500">
                                            Removed on {new Date(install.removal_date).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>

                                <VisitList installId={install.id} />
                            </div>
                        ))}

                        {installs?.length === 0 && (
                            <p className="text-gray-500 italic">No installation history found.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MonitorDetail;
