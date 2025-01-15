/** @odoo-module */
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted } = owl;

export class ChartRender extends Component {
    setup(){
        this.chartRef = useRef("chart")
        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js")
        })

        onMounted(()=> this.renderChart())
    }

    renderChart(){
        if (this.chart) {
            this.chart.destroy()
        }
        this.chart = new Chart(
            this.chartRef.el,
            {
              type: this.props.type,
              data: this.props.config.data,
              options: {
                rensponsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: this.props.title,
                        position: 'bottom'
                    }
                },
              }
            }
        );
    }
}

ChartRender.template = "hr_dashboard.ChartRender"