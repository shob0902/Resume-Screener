import React from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

export default function RadarChart({ dataPoints = [], labels = ['Technical Skills','Experience','Education','Overall'], size = 240 }){
  const data = {
    labels,
    datasets: [{
      label: 'Candidate profile',
      data: dataPoints,
      backgroundColor: (ctx) => {
        // subtle radial gradient using canvas context when available
        const chart = ctx.chart;
        const {ctx: c, chartArea} = chart;
        if (!chartArea) return 'rgba(63,81,181,0.12)';
        const grad = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        grad.addColorStop(0, 'rgba(63,81,181,0.14)');
        grad.addColorStop(1, 'rgba(63,81,181,0.06)');
        return grad;
      },
      borderColor: 'rgba(63,81,181,0.95)',
      borderWidth: 3,
      pointBackgroundColor: 'rgba(255,255,255,1)',
      pointBorderColor: 'rgba(63,81,181,0.95)',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 7,
      fill: true,
      tension: 0.4
    }]
  }

  const options = {
    scales: {
      r: {
        grid: { color: 'rgba(15,23,42,0.06)', circular: true },
        angleLines: { color: 'rgba(15,23,42,0.08)', lineWidth: 1 },
        suggestedMin: 0,
        suggestedMax: 10,
        // hide numeric tick labels (the numbers around the rings)
        ticks: { display: false, stepSize: 2, color: '#64748b', backdropColor: 'transparent', font: { size: 11 } },
        // smaller, bold axis labels positioned slightly away from the chart
        pointLabels: { color: '#0f172a', font: { weight: 700, size: 12 }, padding: 14 }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        callbacks: {
          label: function(context){
            const label = context.label || ''
            const val = context.formattedValue || context.raw || ''
            return `${label}: ${val}/10`
          }
        }
      }
    },
    elements: {
      line: { borderJoinStyle: 'round' },
      point: { hoverBorderWidth: 3 }
    },
    maintainAspectRatio: false,
    responsive: true,
    layout: { padding: 6 }
  }

  return (
    <div style={{width:size, height:size}}>
      <Radar data={data} options={options} />
    </div>
  )
}
