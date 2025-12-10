import React from 'react';
import { Link } from 'react-router-dom';
import { Database, Activity, CheckCircle, Droplets, ArrowRight, Container } from 'lucide-react';
import { useCurrentUser } from '../api/hooks';

const Hub: React.FC = () => {
    const { data: user } = useCurrentUser();

    const modules = [
        {
            name: 'Flow Survey Management',
            description: 'Manage projects, sites, monitors, and installation logistics.',
            path: '/fsm',
            icon: Database,
            color: 'bg-blue-500',
            bg: 'bg-blue-50',
            text: 'text-blue-700',
            hasAccess: user?.access_fsm
        },
        {
            name: 'Flow Survey Analysis',
            description: 'Hydraulic analysis, rainfall event detection, and scatter graphs.',
            path: '/analysis',
            icon: Activity,
            color: 'bg-purple-500',
            bg: 'bg-purple-50',
            text: 'text-purple-700',
            hasAccess: user?.access_fsa
        },
        {
            name: 'Verification',
            description: 'Compare observed data against hydraulic model results.',
            path: '/verification',
            icon: CheckCircle,
            color: 'bg-green-500',
            bg: 'bg-green-50',
            text: 'text-green-700',
            hasAccess: user?.access_verification
        },
        {
            name: 'Water Quality',
            description: 'Analyze WQ samples and correlate with flow data.',
            path: '/wq',
            icon: Droplets,
            color: 'bg-cyan-500',
            bg: 'bg-cyan-50',
            text: 'text-cyan-700',
            hasAccess: user?.access_wq
        },
        {
            name: 'Spill Storage Design',
            description: 'Calculate required tank sizes to meet spill targets.',
            path: '/ssd',
            icon: Container,
            color: 'bg-orange-500',
            bg: 'bg-orange-50',
            text: 'text-orange-700',
            hasAccess: user?.access_ssd
        }
    ];

    return (
        <div className="max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Welcome to FlowBot Hub</h1>
                <p className="text-gray-500 mt-2">Select a workflow to get started.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {modules.filter(m => m.hasAccess || user?.is_superuser).map((module) => {
                    const Icon = module.icon;
                    return (
                        <Link
                            key={module.name}
                            to={module.path}
                            className="group relative overflow-hidden bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
                        >
                            <div className="flex items-start justify-between">
                                <div className={`p-3 rounded-lg ${module.bg} ${module.text} mb-4`}>
                                    <Icon size={24} />
                                </div>
                                <ArrowRight className="text-gray-300 group-hover:text-blue-500 transition-colors" size={20} />
                            </div>

                            <h3 className="text-xl font-bold text-gray-900 mb-2">{module.name}</h3>
                            <p className="text-gray-500">{module.description}</p>

                            <div className={`absolute bottom-0 left-0 w-full h-1 ${module.color} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300`} />
                        </Link>
                    );
                })}
            </div>
        </div>
    );
};

export default Hub;
