import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Database, Activity, CheckCircle, Droplets, LogOut, Menu, X } from 'lucide-react';
import { cn } from '../lib/utils';

const MainLayout: React.FC = () => {
    const location = useLocation();
    const [isCollapsed, setIsCollapsed] = useState(false);

    const navItems = [
        { name: 'Hub', path: '/', icon: LayoutDashboard },
        { name: 'FSM', path: '/fsm', icon: Database },
        { name: 'Analysis', path: '/analysis', icon: Activity },
        { name: 'Verification', path: '/verification', icon: CheckCircle },
        { name: 'Water Quality', path: '/wq', icon: Droplets },
    ];

    return (
        <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
            {/* Sidebar */}
            <aside className={cn(
                "bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out",
                isCollapsed ? "w-16" : "w-64"
            )}>
                <div className={cn(
                    "p-6 border-b border-gray-100 flex items-center",
                    isCollapsed ? "justify-center p-4" : "justify-between"
                )}>
                    {!isCollapsed && (
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                            FlowBot Hub
                        </h1>
                    )}
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? <Menu size={20} /> : <X size={20} />}
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-blue-50 text-blue-700"
                                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                                    isCollapsed && "justify-center"
                                )}
                                title={isCollapsed ? item.name : undefined}
                            >
                                <Icon size={20} />
                                {!isCollapsed && item.name}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-gray-100">
                    <button
                        className={cn(
                            "flex items-center gap-3 px-4 py-3 w-full text-left text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-red-600 rounded-lg transition-colors",
                            isCollapsed && "justify-center"
                        )}
                        title={isCollapsed ? "Sign Out" : undefined}
                    >
                        <LogOut size={20} />
                        {!isCollapsed && "Sign Out"}
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
                    <h2 className="text-lg font-semibold text-gray-800">
                        {navItems.find(i => location.pathname.startsWith(i.path) && i.path !== '/')?.name || 'Hub'}
                    </h2>
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xs">
                            FG
                        </div>
                    </div>
                </header>
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
