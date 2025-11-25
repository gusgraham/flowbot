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

    // Let's assume we have a custom hook or we just use the first one for now 
    // and expand later, OR we use a list of queries.

    // For this implementation, let's create a sub-component that fetches data 
    // and passes it up? No, that's complex.

    // Let's implement a MultiDatasetLoader in this file.

    return (
        <div className="w-full h-[600px] bg-white border border-gray-200 rounded-lg p-4">
            <MultiLineChart datasetIds={datasetIds} datasets={datasets} />
        </div>
    );
};

const MultiLineChart: React.FC<CumulativeDepthChartProps> = ({ datasetIds, datasets }) => {
    // We need to fetch data for each datasetId.
    // Since we can't call hooks in a loop, and the number of datasets varies,
    // we'll use a simple approach: 
    // We'll just render the chart and let it handle empty data, 
    // but we need the data first.

    // A robust way is to use useQueries from react-query, but let's check if we have it.
    // If not, we'll fetch in a useEffect.

    const [allData, setAllData] = React.useState<Record<number, any[]>>({});

    React.useEffect(() => {
        const fetchData = async () => {
            const newData: Record<number, any[]> = {};

            for (const id of datasetIds) {
                try {
                    console.log(`Fetching data for dataset ${id}...`);
                    const response = await fetch(`/api/analysis/rainfall/${id}/cumulative-depth`);

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const result = await response.json();
                    console.log(`Data for dataset ${id}:`, result);

                    if (result.data) {
                        newData[id] = result.data.map((d: any) => ({
                            ...d,
                            timeVal: new Date(d.time).getTime(), // Numeric time for X-axis
                            [`depth_${id}`]: d.cumulative_depth
                        }));
                    }
                } catch (e) {
                    console.error(`Failed to fetch data for dataset ${id}`, e);
                }
            }
            console.log('All processed data:', newData);
            setAllData(newData);
        };

        fetchData();
    }, [datasetIds]);

    // However, for line charts, we can pass separate data arrays to each Line?
    // No, Recharts prefers a single data source.

    // BUT, we can use `data` prop on individual `Line` components!
    // This allows different X-values for each line.
    // We just need to make sure XAxis domain covers everything.

    const combinedData = useMemo(() => {
        // Find min/max time to set domain
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

    return (
        <div style={{ width: '100%', height: '100%', overflow: 'auto' }}>
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
        </div>
    );
};
