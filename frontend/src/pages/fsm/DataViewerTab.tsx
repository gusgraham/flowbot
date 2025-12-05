import React, { useState } from 'react';
import { useInstallTimeseries } from '../../api/hooks';
import { Loader2, Calendar } from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

interface DataViewerTabProps {
    installId: number;
    installType: string;
}

const DataViewerTab: React.FC<DataViewerTabProps> = ({ installId, installType }) => {
    const [dataType, setDataType] = useState<'Raw' | 'Processed'>('Raw');
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');

    const { data, isLoading, error } = useInstallTimeseries(
        installId,
        dataType,
        startDate || undefined,
        endDate || undefined
    );

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-12">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-12">
                <p className="text-red-500">Error loading data: {(error as Error).message}</p>
            </div>
        );
    }

    if (!data || Object.keys(data.variables).length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">No data available for this install</p>
            </div>
        );
    }

    // Prepare chart data by combining all variables with timestamps
    const prepareChartData = () => {
        const timeMap = new Map<string, any>();

        Object.entries(data.variables).forEach(([varName, varData]) => {
            varData.data.forEach((point) => {
                if (!timeMap.has(point.time)) {
                    timeMap.set(point.time, { time: new Date(point.time).getTime() });
                }
                timeMap.get(point.time)![varName] = point.value;
            });
        });

        return Array.from(timeMap.values()).sort((a, b) => a.time - b.time);
    };

    const chartData = prepareChartData();

    const renderFlowMonitorCharts = () => {
        const variables = Object.keys(data.variables);
        const hasDepth = variables.includes('Depth');
        const hasVelocity = variables.includes('Velocity');
        const hasVoltage = variables.includes('Voltage');
        const hasFlow = variables.includes('Flow');

        return (
            <div className="space-y-6">
                {hasDepth && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Depth</h3>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                                        />
                                        <YAxis label={{ value: data.variables.Depth.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey="Depth" stroke="#ef4444" dot={false} strokeWidth={1.5} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Min:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.min?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Max:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.max?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Mean:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.mean?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Points:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.count}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {hasVelocity && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Velocity</h3>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                                        />
                                        <YAxis label={{ value: data.variables.Velocity.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey="Velocity" stroke="#10b981" dot={false} strokeWidth={1.5} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Min:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.min?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Max:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.max?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Mean:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.mean?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Points:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.count}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {(hasVoltage || hasFlow) && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">{hasFlow ? 'Flow' : 'Voltage'}</h3>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                                        />
                                        <YAxis label={{ value: hasFlow ? data.variables.Flow.unit : data.variables.Voltage.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey={hasFlow ? 'Flow' : 'Voltage'} stroke="#3b82f6" dot={false} strokeWidth={1.5} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                {hasFlow && (
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Min:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.min?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Max:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.max?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Mean:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.mean?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Points:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.count}</span>
                                        </div>
                                    </div>
                                )}
                                {hasVoltage && (
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Min:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.min?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Max:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.max?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Mean:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.mean?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Points:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.count}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderRainGaugeChart = () => {
        const varName = 'Rain';
        const varData = data.variables[varName];

        return (
            <div>
                <h3 className="text-lg font-semibold mb-2">{dataType === 'Raw' ? 'Tips' : 'Intensity'}</h3>
                <div className="flex gap-4">
                    <div className="flex-1">
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="time"
                                    type="number"
                                    domain={['dataMin', 'dataMax']}
                                    tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                                />
                                <YAxis label={{ value: varData.unit, angle: -90, position: 'insideLeft' }} />
                                <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                <Legend />
                                <Line type="monotone" dataKey="Rain" stroke="#0ea5e9" dot={false} strokeWidth={1.5} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="w-48 bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                        <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Min:</span>
                                <span className="font-medium">{varData.stats.min?.toFixed(2)} {varData.unit}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Max:</span>
                                <span className="font-medium">{varData.stats.max?.toFixed(2)} {varData.unit}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Mean:</span>
                                <span className="font-medium">{varData.stats.mean?.toFixed(2)} {varData.unit}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Points:</span>
                                <span className="font-medium">{varData.stats.count}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderPumpLoggerChart = () => {
        const varName = 'PumpState';
        const varData = data.variables[varName];

        return (
            <div>
                <h3 className="text-lg font-semibold mb-2">Pump State</h3>
                <div className="flex gap-4">
                    <div className="flex-1">
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="time"
                                    type="number"
                                    domain={['dataMin', 'dataMax']}
                                    tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                                />
                                <YAxis domain={[0, 1]} ticks={[0, 1]} tickFormatter={(val) => val === 1 ? 'On' : 'Off'} />
                                <Tooltip
                                    labelFormatter={(time) => new Date(time).toLocaleString()}
                                    formatter={(value: any) => [value === 1 ? 'On' : 'Off', 'State']}
                                />
                                <Legend />
                                <Line type="stepAfter" dataKey="PumpState" stroke="#8b5cf6" dot={false} strokeWidth={2} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="w-48 bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                        <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Points:</span>
                                <span className="font-medium">{varData.stats.count}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex gap-4 items-end">
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Calendar size={16} className="inline mr-1" />
                        Start Date
                    </label>
                    <input
                        type="datetime-local"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Calendar size={16} className="inline mr-1" />
                        End Date
                    </label>
                    <input
                        type="datetime-local"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setDataType('Raw')}
                            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${dataType === 'Raw'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Raw
                        </button>
                        <button
                            onClick={() => setDataType('Processed')}
                            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${dataType === 'Processed'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Processed
                        </button>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="border-t pt-6">
                {installType === 'Flow Monitor' && renderFlowMonitorCharts()}
                {installType === 'Rain Gauge' && renderRainGaugeChart()}
                {installType === 'Pump Logger' && renderPumpLoggerChart()}
            </div>
        </div>
    );
};

export default DataViewerTab;
