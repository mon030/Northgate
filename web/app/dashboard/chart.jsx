"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
export default function Chart({ rows }) {
  const months = rows.map((r) => ({
    ...r,
    label: new Date(r.alert_month + "-15T12:00:00").toLocaleDateString(
      "en-US",
      { month: "short" },
    ),
  }));
  return (
    <div
      style={{ width: "100%", height: 215 }}
      aria-label="Recorded analyst hours by month"
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 520, height: 215 }}
      >
        <BarChart
          data={months}
          margin={{ left: -18, top: 8, right: 12, bottom: 0 }}
        >
          <CartesianGrid
            vertical={false}
            stroke="#dce4e4"
            strokeDasharray="3 4"
          />
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#53666a", fontSize: 13 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#53666a", fontSize: 12 }}
          />
          <Tooltip formatter={(v) => [v + " h", "Analyst time"]} />
          <Bar
            dataKey="total_analyst_hours"
            fill="#20776e"
            radius={[5, 5, 0, 0]}
            maxBarSize={46}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
