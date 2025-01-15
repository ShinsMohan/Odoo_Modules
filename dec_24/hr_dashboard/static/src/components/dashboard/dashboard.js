/** @odoo-module */

import { registry} from '@web/core/registry';
import { KpiCard, KpiCardLarge, KpiCardMedium } from '../kpi_card/kpi_card';
import { ChartRender } from '../chart/chart_render';
import { useService } from "@web/core/utils/hooks"
import { session } from "@web/session";
const { Component, onWillStart, useRef, onMounted, useState } = owl;

export class HRDashboard extends Component {
    setup(){
        this.orm = useService("orm")
        this.rpc = useService("rpc")
        this.actionService = useService("action")
        this.state = {}
        onWillStart(async ()=>{
            await this.getDashboardData()
        })
    }

    async getDashboardData(){
        const datas = await this.rpc('/hr_dashboard/dashboard_data')

        this.userDomain = datas.user_domain

        this.companyLogo = datas.company_logo
        this.isManager = datas.is_manager
        console.log(this.isManager)
        this.state.leaveRequestCount = datas.tile_data.leave_request_count
        this.state.paySlipCount = datas.tile_data.payslip_count
        this.state.timeSheetCount = datas.tile_data.timesheet_count
        this.state.contractCount = datas.tile_data.contract_count
        this.state.employeeCount = datas.tile_data.employee_count
        this.state.leaveTodayCount = datas.tile_data.leave_today_count
        this.state.leaveMonthCount = datas.tile_data.leave_month_count
        this.state.taskCount = datas.tile_data.task_count
        this.state.pendingTaskCount = datas.tile_data.pending_task_count
        this.state.projectCount = datas.tile_data.project_count

        this.state.employeeName = datas.employee_data.name
        this.state.employeeBirthday = datas.employee_data.birthday
        this.state.employeeGender = datas.employee_data.gender
        this.state.employeeImage = `data:image/png;base64,${datas.employee_data.image}`
        this.state.user = datas.employee_data.name
        this.state.userImageUrl = `data:image/png;base64,${datas.employee_data.image}`;
        this.state.jobTitle = datas.employee_data.job_title
        this.state.employeeAge = datas.employee_data.age
        this.state.employeeDepartment = datas.employee_data.department
        this.state.employeeMobile = datas.employee_data.mobile_phone
        this.state.employeeEmail = datas.employee_data.work_email
        this.state.employeeExperience = datas.employee_data.experience

        let departmentEmployeeGraphData = datas.graph_data.department_employees
        this.state.departmentEmployees = {
            data: {
                labels: departmentEmployeeGraphData.map(d => d.label),
                datasets: [{
                    label: 'Employees',
                    data: departmentEmployeeGraphData.map(d => d.value),

                }]
            }
        }

        let departmentMonthLeavesGraphData = datas.graph_data.department_month_leaves
        this.state.departmentMonthLeaves = {
            data: {
                labels: departmentMonthLeavesGraphData.map(d => d.name.en_US),
                datasets: [{
                    label: 'Number of Days',
                    data: departmentMonthLeavesGraphData.map(d => d.number_of_days),
                    spacing: 5,
                    borderRadius: 20

                }]
            }
        }

        let myLeavesGraphData = datas.graph_data.my_leaves
        this.state.myLeaves = {
            data: {
                labels: myLeavesGraphData.map(d => d.date),
                datasets: [{
                    label: 'Number of Days',
                    data: myLeavesGraphData.map(d => d.number_of_days),
                }]
            }
        }

        let myTimesheetsGraphData = datas.graph_data.my_timesheets
        this.state.myTimesheets = {
            data: {
                labels: myTimesheetsGraphData.map(d => d.date),
                datasets: [{
                    label: 'Hours',
                    data: myTimesheetsGraphData.map(d => d.hour),
                }]
            }
        }

        this.state.upcomingBirthDays = datas.upcoming_birthdays
        this.state.pendingLeaves = datas.pending_leaves
    }

    async openModelView(model, domain, views, context = null, view_id = null) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: model,
            res_model: model,
            domain,
            views: views,
            context: context,
            view_id: view_id,
        })
    }
    

    async viewPaySlips(){
        await this.openModelView("hr.payslip", 
            this.userDomain.payslip_domain,
            [[false, "list"], [false, "form"]]
            )
    }

    async viewTimeSheets(){
        await this.openModelView("account.analytic.line", 
            this.userDomain.timesheet_domain,
            [[false, "grid"], [false, "list"], [false, "form"], [false, "kanban"], [false, "pivot"], [false, "graph"]],
            {'group_expand': true,"is_timesheet": 1,'grid_range': 'day'},
            ['timesheet_grid.timesheet_view_grid_by_employee_editable_manager']
            )
    }
    

    async viewContracts(){
        await this.openModelView("hr.contract", 
            this.userDomain.contract_domain,
            [[false, "list"], [false, "form"], [false, "kanban"]]
            )
    }
    

    async viewEmployees(){
        await this.openModelView("hr.employee", 
            this.userDomain.employee_domain, 
            [[false, "kanban"], [false, "list"], [false, "form"]]
            )
    }

    async viewLeaveRequests(){
        await this.openModelView("hr.leave", 
            this.userDomain.leave_request_domain, 
            [[false, "list"], [false, "form"]],
            {'search_default_waiting_for_me': 1, 'search_default_waiting_for_me_manager': 2, 'hide_employee_name': 1, 'holiday_status_display_name': false}
            )
    }

    async viewLeaveToday(){
        await this.openModelView("hr.leave", 
            this.userDomain.leave_today_domain, 
            [[false, "list"], [false, "form"]]
            )
    }

    async viewLeaveMonth(){
        await this.openModelView("hr.leave", 
            this.userDomain.leave_month_domain, 
            [[false, "list"], [false, "form"]]
            )
    }

    async viewTasks(){
        await this.openModelView("project.task", 
            this.userDomain.task_domain, 
            [[false, "list"], [false, "form"], [false, "kanban"], [false, "calendar"]],
            {'search_default_open_tasks': 1}
            )
    }

    async viewPendingTasks(){
        await this.openModelView("project.task", 
            this.userDomain.pending_task_domain, 
            [[false, "list"], [false, "form"], [false, "kanban"], [false, "calendar"]],
            {'search_default_open_tasks': 1}
            )
    }

    async viewProjects(){
        await this.openModelView("project.project", 
            this.userDomain.project_domain, 
            [[false, "kanban"], [false, "list"], [false, "form"]]
            )
    }
}

HRDashboard.template = "hr_dashboard.HRDashboard"
HRDashboard.components = { KpiCard, KpiCardLarge, KpiCardMedium, ChartRender }

registry.category("actions").add("hr_dashboard", HRDashboard)
