import React, { useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';
export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
    constructor(props: any) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(_: any) {
        return { hasError: true };
    }

    componentDidCatch(error: any, info: any) {
        console.error('ErrorBoundary caught an error', error, info);
    }

    render() {
        if (this.state.hasError) {
            return <div className="text-red-600">Something went wrong while rendering the chart.</div>;
        }
        return this.props.children;
    }
}


interface CumulativeDepthChartProps {
    datasetIds: number[];
    datasets: any[]; // Pass full dataset objects to get names/colors
}

const COLORS = [
    "#00BCD4", // Cyan
    "#E91E63", // Pink
    "#4CAF50", // Green
    "#9C27B0", // Purple
    "#FF9800", // Orange
    "#3F51B5", // Indigo
    "#795548", // Brown
    "#607D8B", // Blue Grey
    "#F44336", // Red
    "#2196F3", // Blue
];

export const CumulativeDepthChart: React.FC<CumulativeDepthChartProps> = ({ datasetIds, datasets }) => {
    // Fetch data for all selected datasets
    // In a real app, we might want to use useQueries for parallel fetching
    // For now, we'll map and render what we have

    // We need a way to combine data from multiple queries. 
    // Since hooks can't be called in loops/callbacks, we'll assume the parent 
    // or a wrapper handles fetching, OR we use a custom hook that handles multiple IDs.

    // Actually, let's just fetch for each ID. 
    // Limitation: React Query hooks must be top-level. 
    // We'll create a wrapper component or just fetch one by one if the list is small.
    // Better approach: The parent component should probably fetch or we use a component that takes a single ID,
    // but we want to plot them on the SAME chart.

    // we'll use a simple approach: 
    // We'll just render the chart and let it handle empty data, 
    // but we need the data first.
    // We just need to make sure XAxis domain covers everything.

    const [allData, setAllData] = React.useState<Record<number, any[]>>({});
    const [isLoading, setIsLoading] = React.useState(false);

    React.useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            const newData: Record<number, any[]> = {};
            // Only handle rainfall datasets (check 'variable' field)
            const rainfallIds = datasetIds.filter(id => {
                const ds = datasets.find(d => d.id === id);
                console.log(`Dataset ${id}:`, ds); // Debug log
                return ds && ds.variable && ds.variable.toLowerCase() === 'rainfall';
            });
            console.log('Filtered rainfall IDs:', rainfallIds);
            for (const id of rainfallIds) {
                try {
                    console.log(`Fetching data for dataset ${id}...`);
                    const response = await fetch(`/api/fsa/rainfall/${id}/cumulative-depth`);
                    if (!response.ok) {
                        console.error(`HTTP error for dataset ${id}: ${response.status}`);
                        continue;
                    }
                    const result = await response.json();
                    console.log(`Data for dataset ${id}:`, result);
                    if (result && result.data) {
                        newData[id] = result.data.map((d: any) => ({
                            ...d,
                            timeVal: new Date(d.time).getTime(),
                            [`depth_${id}`]: d.cumulative_depth,
                        }));
                    } else {
                        console.warn(`No data field for dataset ${id}`);
                    }
                } catch (e) {
                    console.error(`Failed to fetch data for dataset ${id}`, e);
                }
            }
            console.log('All processed data:', newData);
            setAllData(newData);
            setIsLoading(false);
        };
        fetchData();
    }, [datasetIds, datasets]);

    // Compute combined time domain for XAxis
    const combinedData = React.useMemo(() => {
        let minTime = Infinity;
        let maxTime = -Infinity;
        Object.values(allData).forEach(data => {
            data.forEach(p => {
                if (p.timeVal < minTime) minTime = p.timeVal;
                if (p.timeVal > maxTime) maxTime = p.timeVal;
            });
        });
        return { minTime, maxTime };
    }, [allData]);

    if (datasetIds.length === 0) {
        return <div className="flex items-center justify-center h-full text-gray-500">Select a rainfall dataset to view cumulative depth</div>;
    }

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
                <p>Loading cumulative depth data...</p>
                <p className="text-sm mt-2">This may take a moment for large datasets</p>
            </div>
        );
    }

    return (
        <div style={{ width: '100%', height: '100%', overflow: 'auto' }}>
            <ErrorBoundary>
                <LineChart width={1000} height={500}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="timeVal"
                        type="number"
                        domain={[combinedData.minTime, combinedData.maxTime]}
                        tickFormatter={(tick) => format(new Date(tick), 'dd/MM HH:mm')}
                        label={{ value: "Time", position: "insideBottom", offset: -5 }}
                    />
                    <YAxis
                        label={{ value: "Cumulative Depth (mm)", angle: -90, position: "insideLeft" }}
                    />
                    <Tooltip
                        labelFormatter={(label) => format(new Date(label), 'dd/MM/yyyy HH:mm')}
                        formatter={(value: number) => [value.toFixed(2) + " mm"]}
                    />
                    <Legend verticalAlign="top" height={36} />

                    {datasetIds.map((id, index) => {
                        const dataset = datasets.find(d => d.id === id);
                        const name = dataset ? dataset.name : `Dataset ${id}`;
                        const color = COLORS[index % COLORS.length];
                        const data = allData[id] || [];

                        if (data.length === 0) return null;

                        return (
                            <Line
                                key={id}
                                data={data}
                                type="monotone"
                                dataKey={`depth_${id}`}
                                name={name}
                                stroke={color}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 6 }}
                            />
                        );
                    })}
                </LineChart>
            </ErrorBoundary>
        </div>
    );
};
