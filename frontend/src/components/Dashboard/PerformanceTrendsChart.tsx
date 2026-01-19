import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { PerformanceTrend } from '../../types';

interface PerformanceTrendsChartProps {
  data: PerformanceTrend[];
  height?: number;
}

const toDate = (iso: string) => {
  const s = iso.trim();
  // If backend sends naive timestamps, treat them as UTC.
  const normalized = /z$|[+-]\d{2}:?\d{2}$/i.test(s) ? s : `${s}Z`;
  return new Date(normalized);
};

const formatHour = (iso: string) => {
  const d = toDate(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
};

const formatLabelDateTime = (iso: string) => {
  const d = toDate(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};

const formatDuration = (ms: number) => {
  if (!Number.isFinite(ms)) return '0ms';
  if (ms === 0) return '0ms';
  if (ms < 1) return `${(ms * 1000).toFixed(0)}µs`;
  if (ms < 10) return `${ms.toFixed(3)}ms`;
  return `${ms.toFixed(2)}ms`;
};

export default function PerformanceTrendsChart({ data, height = 260 }: PerformanceTrendsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <TrendingUp className="w-10 h-10 mx-auto mb-2 text-gray-400" />
          <p>No trend data yet</p>
        </div>
      </div>
    );
  }

  const chartData = data.map((p) => ({
    ...p,
    hour: formatHour(p.timestamp),
    _label: formatLabelDateTime(p.timestamp),
    avg_time: typeof p.avg_time === 'number' ? p.avg_time : 0,
    slow_queries: typeof p.slow_queries === 'number' ? p.slow_queries : 0,
    total_queries: typeof p.total_queries === 'number' ? p.total_queries : 0,
  }));

  const maxY = Math.max(...chartData.map((x) => x.avg_time), 0);
  const yMax = maxY > 0 ? maxY * 1.2 : 1;
  const maxCount = Math.max(...chartData.map((x) => x.total_queries), 0);
  const countMax = maxCount > 0 ? Math.ceil(maxCount * 1.2) : 1;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
        <XAxis dataKey="hour" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
        <YAxis
          yAxisId="left"
          stroke="#9CA3AF"
          style={{ fontSize: '12px' }}
          domain={[0, yMax]}
          allowDecimals
          tickFormatter={(v) => formatDuration(Number(v))}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#9CA3AF"
          style={{ fontSize: '12px' }}
          domain={[0, countMax]}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
            color: '#F9FAFB',
          }}
          formatter={(value: any, name: string) => {
            if (name === 'avg_time') return [formatDuration(Number(value)), 'Avg time'];
            if (name === 'slow_queries') return [value, 'Slow queries'];
            if (name === 'total_queries') return [value, 'Total queries'];
            return [value, name];
          }}
          labelFormatter={(_: any, payload: any[]) => {
            const item = payload?.[0]?.payload;
            return item?._label ? `Time: ${item._label}` : 'Time';
          }}
        />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        <Line
          type="monotone"
          dataKey="avg_time"
          yAxisId="left"
          name="Avg time"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={{ r: 2, fill: '#3B82F6' }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="total_queries"
          yAxisId="right"
          name="Total queries"
          stroke="#10B981"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
