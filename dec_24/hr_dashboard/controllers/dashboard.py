import datetime
from odoo import http
from odoo.http import request
from datetime import timedelta, datetime, date, time
from dateutil.rrule import rrule, DAILY
import calendar
from dateutil.relativedelta import relativedelta

class FarmDashboard(http.Controller): 

    def _get_login_employee(self):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        return employee
    
    def _get_user_domain(self):
        employee = self._get_login_employee()

        # Employee Domain based on User Role
        if request.env.user.user_has_groups('hr.group_hr_manager') or request.env.user.user_has_groups('hr.group_hr_user'):
            employee_domain = []
        # elif request.env.user.user_has_groups('hr.group_hr_user'):
        #     if employee:
        #         employee_domain = [['department_id', '=', employee.department_id.id] if employee.department_id else ['id', '=', employee.id]]
        #     else:
        #         employee_domain = [['department_id', '=', False]]
        else:
            employee_domain = [['id', '=', employee.id if employee else False]]

        # Payslip Domain based on User Role
        if request.env.user.user_has_groups('hr_payroll.group_hr_payroll_manager') or request.env.user.user_has_groups('hr_payroll.group_hr_payroll_user'):
            payslip_domain = []
        elif request.env.user.user_has_groups('hr.group_hr_payroll_employee_manager'):
            if employee:
                payslip_domain = [['employee_id.department_id', '=', employee.department_id.id] if employee.department_id else ['employee_id', '=', employee.id]]
            else:
                payslip_domain = [['employee_id.department_id', '=', False]]
        else:
            payslip_domain = [['employee_id', '=', employee.id if employee else False]]

        # Timesheet Domain based on User Role
        today = date.today()
        # start_date = today.replace(day=1)
        # month_end = calendar.monthrange(today.year, today.month)[1]
        # end_date = today.replace(day=month_end)
        if request.env.user.user_has_groups('hr_timesheet.group_timesheet_manager') or request.env.user.user_has_groups('hr_timesheet.group_hr_timesheet_approver'):
            timesheet_domain = [['project_id', '!=', False]]
            timesheet_count_domain = [['project_id', '!=', False], ['date', '=', today]]
        else:
            timesheet_domain = [['project_id', '!=', False], ['user_id', '=', request.env.user.id]]
            timesheet_count_domain = [['project_id', '!=', False], ['date', '=', today], ['user_id', '=', request.env.user.id]]
        # Contract Domain based on User Role
        if request.env.user.user_has_groups('hr_contract.group_hr_contract_manager'):
            contract_domain = [['state', '=', 'open']]
        elif request.env.user.user_has_groups('hr_contract.group_hr_contract_employee_manager'):
            if employee:
                contract_domain = [['state', '=', 'open'], ['employee_id.department_id', '=', employee.department_id.id] if employee.department_id else ['employee_id', '=', employee.id]]
            else:
                contract_domain = [['state', '=', 'open'], ['employee_id.department_id', '=', False]]
        else:
            contract_domain = [['state', '=', 'open'], ['employee_id', '=', employee.id if employee else False]]

         # Leave Domain based on User Role
        if request.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or request.env.user.user_has_groups('hr_holidays.group_hr_holidays_user'):
            leave_request_domain = [['state', 'not in', ['validate', 'refuse']]]
        else:
            leave_request_domain = [['employee_id', '=', employee.id if employee else False], ['state', 'not in', ['validate', 'refuse']]]

        # Leave today Domain based on User Role
        if request.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or request.env.user.user_has_groups('hr_holidays.group_hr_holidays_user'):
            leave_today_domain = [['state', 'not in', ['refuse']], ['request_date_from', '<=', datetime.today()], 
                                  ['request_date_to', '>=', datetime.today()]]
        else:
            leave_today_domain = [['employee_id', '=', employee.id if employee else False], ['state', 'not in', ['refuse']], 
                                  ['request_date_from', '>=', datetime.today()], ['request_date_to', '<=', datetime.today()]]
            
        # Leave this month Domain based on User Role
        if request.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or request.env.user.user_has_groups('hr_holidays.group_hr_holidays_user'):
            leave_today_domain = [['state', 'not in', ['refuse']], ['request_date_from', '<=', datetime.today()], 
                                  ['request_date_to', '>=', datetime.today()]]
        else:
            leave_today_domain = [['employee_id', '=', employee.id if employee else False], ['state', 'not in', ['refuse']], 
                                  ['request_date_from', '>=', datetime.today()], ['request_date_to', '<=', datetime.today()]]
            
        # Project Task Domain based on User Role
        if request.env.user.user_has_groups('project.group_project_manager'):
            task_domain = [['planned_date_begin', '<=', today], ['date_deadline', '>=', today]]
            pending_task_domain = [['date_deadline', '<', today], ['state', 'not like', 'done']]
            tasks = request.env['project.task'].search(task_domain)
            projects = tasks.mapped('project_id')
            project_domain = [['id', 'in', projects.ids]]
        else:
            task_domain = [['planned_date_begin', '<=', today], ['date_deadline', '>=', today], ['user_ids', 'in', request.env.user.ids]]
            pending_task_domain = [['date_deadline', '<', today], ['user_ids', 'in', request.env.user.ids], ['state', 'not like', 'done']]
            tasks = request.env['project.task'].search(task_domain)
            projects = tasks.mapped('project_id')
            project_domain = [['id', 'in', projects.ids]]
            
        
        return {
            'employee_domain': employee_domain,
            'payslip_domain': payslip_domain,
            'timesheet_domain': timesheet_domain,
            'timesheet_count_domain': timesheet_count_domain,
            'contract_domain': contract_domain,
            'leave_request_domain': leave_request_domain,
            'leave_today_domain': leave_today_domain,
            'project_domain': project_domain,
            'task_domain': task_domain, 
            'pending_task_domain': pending_task_domain
        } 
    
    def _get_department_month_leaves(self):
        first_day = date.today().replace(day=1)
        last_day = (date.today() + relativedelta(months=1, day=1)) - timedelta(1)
        query = """
        select d.id, d.name, sum(l.number_of_days) as number_of_days
        from hr_leave l
        left join hr_department d on d.id = l.department_id 
        WHERE (l.date_from::DATE,l.date_to::DATE) 
        OVERLAPS (%s, %s)
        and  state not in ('draft', 'refuse')
        group by d.id
        """
        cr = request._cr
        cr.execute(query, [first_day, last_day])
        result = cr.dictfetchall()
        return result
    
    def _get_myleaves(self, employee_id: int):
        first_day = date.today().replace(day=1)
        last_day = (date.today() + relativedelta(months=1, day=1)) - timedelta(1)
        query = """
        SELECT 
            l.id, 
            TO_CHAR(l.request_date_from, 'DD-MM-YYYY') AS date, 
            e.name, 
            l.number_of_days AS number_of_days
        FROM 
            hr_leave l
        LEFT JOIN 
            hr_employee e ON e.id = l.employee_id 
        WHERE 
            (l.date_from::DATE, l.date_to::DATE) OVERLAPS (%s, %s)
            AND state NOT IN ('draft', 'refuse') AND l.employee_id = %s
        ORDER BY 
            l.date_from;

        """
        cr = request._cr
        cr.execute(query, [first_day, last_day, employee_id])
        result = cr.dictfetchall()
        return result
    
    def _get_my_timesheets(self, employee_id: int):
        today = date.today()
        seventh_day = today - timedelta(days=7)
        query = """
        WITH date_series AS (
            SELECT 
                generate_series(%s::date, %s::date, interval '1 day') AS date
        )
        SELECT  
            TO_CHAR(ds.date, 'DD-MM') AS date, 
            COALESCE(SUM(aal.unit_amount), 0) AS hour
        FROM 
            date_series ds
        LEFT JOIN 
            account_analytic_line aal 
        ON 
            ds.date = aal.date
            AND aal.project_id IS NOT NULL 
            AND aal.employee_id = %s
        GROUP BY 
            ds.date
        ORDER BY 
            ds.date;

        """
        cr = request._cr
        cr.execute(query, [seventh_day, today, employee_id])
        result = cr.dictfetchall()
        return result
    
    def _get_graph_data(self):
        user_domain = self._get_user_domain()
        employee = self._get_login_employee()
        # Get Department Employees
        department_employees = request.env['hr.employee'].sudo().read_group(
            domain=user_domain['employee_domain'],
            fields=['id', 'department_id'],
            groupby=['department_id'],
        )
        department_list = []
        for department_employee in department_employees:
            department_list.append({'label': department_employee['department_id'][1] if department_employee['department_id'] else 'No Department', 'value': department_employee['department_id_count']})
        
        month_leaves = self._get_department_month_leaves()
        # Get My Leaves and My Timesheets for the current employee
        my_leaves = self._get_myleaves(employee.id if employee else 0)
        my_timesheets = self._get_my_timesheets(employee.id if employee else 0)

        return {
            'department_employees': department_list,
            'department_month_leaves': month_leaves,
            'my_leaves': my_leaves,
            'my_timesheets': my_timesheets,
        }
    
    def _calculate_age(self, birthdate: date) -> int:
        today = datetime.today()
        # Calculate the difference in years
        age = today.year - birthdate.year
        # Check if the birthday has not yet occurred this year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
        return age
    
    def _get_upcoming_birthdays(self):
        today = date.today()
        end_date = today + timedelta(days=30)

        today_str = today.strftime('%m-%d')
        end_date_str = end_date.strftime('%m-%d')

        # SQL query to get employees with birthdays in the next 30 days
        query = """
            SELECT id, name, birthday::date,
            (DATE_TRUNC('year', CURRENT_DATE) + (birthday - DATE_TRUNC('year', birthday)))::date - CURRENT_DATE AS age_difference
            FROM hr_employee
            WHERE 
                TO_CHAR(birthday, 'MM-DD') >= %s
                AND TO_CHAR(birthday, 'MM-DD') <= %s
                AND birthday IS NOT NULL
            ORDER BY TO_CHAR(birthday, 'MM-DD');
        """

        cr = request._cr
        cr.execute(query, (today_str, end_date_str))
        employees = cr.fetchall()
        birthday_list = []
        for employee in employees:
            birthday_list.append({
                'id': employee[0],
                'name': employee[1],
                'image': request.env['hr.employee'].sudo().browse([employee[0]]).image_128,
                'birthday': employee[2].strftime('%d-%m-%Y'),
                'days': employee[3]
            })
        return birthday_list
    
    def _get_month_leaves(self):
        first_day = date.today().replace(day=1)
        last_day = (date.today() + relativedelta(months=1, day=1)) - timedelta(
            1)
        query = """
                select id
                from hr_leave
                WHERE (hr_leave.date_from::DATE,hr_leave.date_to::DATE) 
                OVERLAPS (%s, %s)
                and  state not in ('draft', 'refuse')"""
        cr = request._cr
        cr.execute(query, (first_day, last_day))
        leaves_this_month = cr.fetchall()
        return leaves_this_month   

    def _get_employee_pending_leaves(self, employee_id: int):
        query = """ SELECT 
                        e.id as employee_id, e.name as employee, hlt.id as leave_type_id, hlt.name as leave_type, sum(number_of_days) as number_of_days 
                    FROM 
                        hr_leave_report hlr
                    LEFT JOIN 
                        hr_employee e ON e.id = hlr.employee_id
                    LEFT JOIN 
                        hr_leave_type hlt ON hlt.id = hlr.holiday_status_id
                    WHERE
                        hlt.requires_allocation = 'yes' AND e.id = %s
                    GROUP BY 
                        e.id, hlt.id
                    ORDER BY 
                        e.name, hlt.name 
                """ 
        cr = request._cr
        cr.execute(query, [employee_id])
        leaves_pendings = cr.dictfetchall()
        return leaves_pendings

    
    @http.route('/hr_dashboard/user_domain', auth='public', type='json')
    def get_user_domain(self):
        return self._get_user_domain()
    
    @http.route('/hr_dashboard/dashboard_data', auth='public', type='json')
    def get_dashboard_data(self):
        # Check whether user is HR Manager or not
        is_manager = 0
        if request.env.user.user_has_groups('hr.group_hr_manager') or request.env.user.user_has_groups('hr.group_hr_user'):
            is_manager = 1
        
        user_domain = self._get_user_domain()
        # Get Employee Data
        employee = self._get_login_employee()
        if employee:
            experience = ''
            if employee.joining_date:
                diff = relativedelta(datetime.today(),
                                     employee.joining_date)
                years = diff.years
                months = diff.months
                days = diff.days
                experience = '{} years {} months {} days'.format(years, months, days)
            employee_data = {
                'id': employee.id,
                'name': employee.name,
                'image': employee.image_1920,
                'department': employee.department_id.name if employee.department_id else 'No Department',
                'job_title': employee.job_id.name if employee.job_id else 'No Job Title',
                'work_email': employee.work_email,
                'mobile_phone': employee.private_phone,
                'birthday': employee.birthday.strftime('%d-%m-%Y') if employee.birthday else '',
                # 'hire_date': employee.hire_date.strftime('%d-%m-%Y') if employee.hire_date else '',
                'gender': employee.gender.capitalize() if employee.gender else '',
                'age': self._calculate_age(employee.birthday) if employee.birthday else '',
                'experience': experience
            }
        else:
            employee_data = {
                'id': '',
                'name': '',
                'image': None,
                'department': '',
                'job_title': '',
                'work_email': '',
                'mobile_phone': '',
                'birthday': '',
                'hire_date': '',
                'gender': '',
                'age': '',
                'experience': ''
            }

        # Get Tiles Data
        employee_count = request.env['hr.employee'].sudo().search_count(user_domain['employee_domain'])
        payslip_count = request.env['hr.payslip'].sudo().search_count(user_domain['payslip_domain'])
        timesheet_count = sum(request.env['account.analytic.line'].sudo().search(user_domain['timesheet_count_domain']).mapped('unit_amount'))
        contract_count = request.env['hr.contract'].sudo().search_count(user_domain['contract_domain'])
        leave_request_count = request.env['hr.leave'].sudo().search_count(user_domain['leave_request_domain'])
        leave_today_count = request.env['hr.leave'].sudo().search_count(user_domain['leave_today_domain'])
        task_count = request.env['project.task'].sudo().search_count(user_domain['task_domain'])
        project_count = request.env['project.project'].sudo().search_count(user_domain['project_domain'])
        pending_task_count = request.env['project.task'].sudo().search_count(user_domain['pending_task_domain'])

        # Get monthly leaves
        leave_month = self._get_month_leaves()
        leave_month_ids = [leave[0] for leave in leave_month]
        user_domain['leave_month_domain'] = [['id', 'in', leave_month_ids if leave_month_ids else False]]

        tile_data = {
            'employee_count': employee_count if employee_count > 0 else 0,
            'payslip_count': payslip_count if payslip_count > 0 else 0,
            'timesheet_count': timesheet_count if timesheet_count > 0 else 0,
            'contract_count': contract_count if contract_count > 0 else 0,
            'leave_request_count': leave_request_count if leave_request_count > 0 else 0,
            'leave_today_count': leave_today_count if leave_today_count > 0 else 0,
            'task_count': task_count if task_count > 0 else 0,
            'project_count': project_count if project_count > 0 else 0,
            'pending_task_count': pending_task_count if pending_task_count > 0 else 0,
            'leave_month_count': len(leave_month) if leave_month else 0
        }

        # Get Graph Data
        graph_data = self._get_graph_data()

        # Get Upcoming Birthdays
        upcoming_birthdays = self._get_upcoming_birthdays()

        pendling_leaves = self._get_employee_pending_leaves(employee.id if employee else 0)

        return {
            'tile_data': tile_data,
            'graph_data': graph_data,
            'employee_data': employee_data,
            'user_domain': user_domain,
            'upcoming_birthdays': upcoming_birthdays,
            'pending_leaves': pendling_leaves,
            'company_logo': request.env.company.logo,
            'is_manager': is_manager
        }

    
    @http.route('/hr_dashboard/graph_data', auth='public', type='json')
    def get_graph_data(self):
        user_domain = self._get_user_domain()
        # Get Department Employees
        department_employees = request.env['hr.employee'].read_group(
            domain=user_domain['employee_domain'],
            fields=['id', 'department_id'],
            groupby=['department_id'],
        )
        department_list = []
        for department_employee in department_employees:
            department_list.append({'label': department_employee['department_id'][1] if department_employee['department_id'] else 'No Department', 'value': department_employee['department_id_count']})
        return {
            'department_employees': department_list,
        }
