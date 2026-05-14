'use client';

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TypeDistributionItem } from '@/lib/api';

const COLORS = ['#991b1b', '#dc2626', '#ef4444', '#f87171', '#fca5a5', '#b91c1c'];

export interface TypeDistributionChartProps {
  data: TypeDistributionItem[];
}

export function TypeDistributionChart({ data }: TypeDistributionChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-md border border-gray-200 bg-gray-50" style={{ minHeight: 220 }}>
        <p className="text-sm font-medium text-gray-500">No distribution data.</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="type"
          cx="50%"
          cy="50%"
          outerRadius={80}
          innerRadius={45}
          paddingAngle={2}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [value, 'Incidents']}
          contentStyle={{ fontSize: 12, borderRadius: 4, border: '1px solid #d8dbe0' }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11 }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}