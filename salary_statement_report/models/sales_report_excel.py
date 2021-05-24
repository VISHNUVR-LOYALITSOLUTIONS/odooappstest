import datetime
from odoo.exceptions import UserError
from datetime import datetime, date
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class salary_statementXls(models.AbstractModel):
    _name = 'report.salary_statement_report.payroll_salary_statement_xls'
    _inherit = 'report.report_xlsx.abstract'

    def get_sale(self, data):

        lines = []

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        target_move = data['form']['target_move']

        sl = 0
        if target_move==False:


            query = '''

            select dd.id,
                (dd.employee_name) as employee_name,
                (dd.designation) as designation,
                (dd.department) as department,
                (dd.basic_salary) as basic_salary,
                (dd.no_of_days) as no_of_days,
                (dd.working_days) as working_days,
                (dd.no_of_days)-(dd.working_days) as leave_days,
                (dd.basic_salary/dd.no_of_days)*(dd.working_days) as salary_for_the_month,
                (dd.less_tds) as less_tds,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))-(dd.less_tds) as salary_payable,
                dd.other_deduction as other_deduction,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))*0.75/100 as esi_employee_deduction,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))*3.25/100 as esi_employer_contribution,
                dd.canteen_expense as canteen_expense,
                dd.esi_deduction as esi_deduction,
                
                
                dd.net_amount as net_amount
                
                from

            ((select hre.id as id,hre.name as employee_name,
                    max(hrj.name) as designation,
                    max(hp.name) as department,
                     sum(case when hrpl.name='Basic Salary' then hrpl.total else 0 end) as basic_salary, 
                     date_part('days',date_trunc('month',to_date(%s,'YYYY-MM-DD'))+'1 MONTH'::INTERVAL-
                             date_trunc('month',to_date(%s,'YYYY-MM-DD'))) as no_of_days,
              sum(case when hrpl.code ~~* 'TDS%%' then hrpl.total else 0 end) as less_tds,
              sum(case when hrpl.code='NET' then hrpl.total else 0 end) as net_amount,
              sum(case when hrpl.code='ESI' then hrpl.total else 0 end) as esi_deduction,

               sum(case when hrpl.code='Can Ex' then hrpl.total else 0 end) as canteen_expense
              
                        
            
                        from hr_payslip_line as hrpl
                left join hr_payslip as hrp on hrp.id=hrpl.slip_id
                left join hr_employee as hre on hre.id=hrp.employee_id
                left join hr_department as hp on hp.id=hre.department_id
                left join hr_job as hrj on hrj.id=hre.job_id
                
                where to_char(date_trunc('day',hrp.date_from),'YYYY-MM-DD')::date between %s and %s
              and hrp.company_id=%s 
            and (hrj.name not in ('Health Care Assistance') OR hrj.name is null)
              and hrp.state in ('verify','done')
                
                group by hre.id) as a
                
                left join
                (select sum(hw.number_of_days) as working_days,h.employee_id as employee_id from hr_payslip as h
                left join hr_payslip_worked_days as hw on h.id=hw.payslip_id
                where to_char(date_trunc('day',h.date_from),'YYYY-MM-DD')::date between %s and %s
                 and h.company_id=%s
                 and h.state in ('verify','done')
                group by h.employee_id)as b on a.id=b.employee_id
             
             left join
             (select hl.employee_id as em_id,
              sum(case when hl.code !~~* 'TDS%%' and hl.code<>'Can Ex' and hl.code<>'ESI' and hc.name='Deduction'  then hl.total else 0 end) as other_deduction
             from hr_payslip_line as hl
              left join hr_payslip as hp on hp.id=hl.slip_id
              left join hr_salary_rule_category as hc on hc.id=hl.category_id
              where to_char(date_trunc('day',hp.date_from),'YYYY-MM-DD')::date between %s and %s
              and hp.company_id=%s
                 and hp.state in ('verify','done')
              
              group by hl.employee_id
             )as c on a.id=c.em_id
            
            )dd     
              
              '''

            self.env.cr.execute(query, (
                date_to,date_to,
                date_from,date_to,company_id,
                date_from,date_to, company_id,
                date_from, date_to, company_id,
            ))
            for row in self.env.cr.dictfetchall():
                sl += 1

                employee_name = row['employee_name'] if row['employee_name'] else " "
                designation = row['designation'] if row['designation'] else " "
                department = row['department'] if row['department'] else " "
                basic_salary = row['basic_salary'] if row['basic_salary'] else 0.0
                no_of_days = row['no_of_days'] if row['no_of_days'] else 0.0
                working_days = row['working_days'] if row['working_days'] else 0.0
                # total_amount = row['total_amount'] if row['total_amount'] else 0
                # sale_new_date = datetime.strptime(str(saledate), '%Y-%m-%d').date().strftime('%d-%m-%Y')
                leave_days = row['leave_days'] if row['leave_days'] else 0.0
                salary_for_the_month = row['salary_for_the_month'] if row['salary_for_the_month'] else 0.0
                less_tds = row['less_tds'] if row['less_tds'] else 0.0
                salary_payable = row['salary_payable'] if row['salary_payable'] else 0.0
                other_deduction = row['other_deduction'] if row['other_deduction'] else 0.0
                esi_employee_deduction = row['esi_employee_deduction'] if row['esi_employee_deduction'] else 0.0
                esi_employer_contribution = row['esi_employer_contribution'] if row['esi_employer_contribution'] else 0.0
                canteen_expense = row['canteen_expense'] if row['canteen_expense'] else 0.0
                net_amount = row['net_amount'] if row['net_amount'] else 0.0
                esi_deduction = row['esi_deduction'] if row['esi_deduction'] else 0.0
                res = {
                    'sl_no': sl,
                    'esi_deduction':esi_deduction if esi_deduction else 0.0,
                    'employee_name': employee_name if employee_name else " ",
                    'designation': designation if designation else " ",
                    'department': department if department else " ",
                    'basic_salary': basic_salary if basic_salary else 0.0,
                    'no_of_days': no_of_days if no_of_days else 0.0,
                    'working_days': working_days if working_days else 0.0,
                    'leave_days': leave_days if leave_days else 0.0,
                    'salary_for_the_month': salary_for_the_month if salary_for_the_month else 0.0,
                    'less_tds': less_tds if less_tds else 0.0,
                    'salary_payable': salary_payable if salary_payable else 0.0,
                    'other_deduction': other_deduction if other_deduction else 0.0,
                    'esi_employee_deduction': esi_employee_deduction if esi_employee_deduction else 0.0,
                    'esi_employer_contribution': esi_employer_contribution if esi_employer_contribution else 0.0,
                    'canteen_expense': canteen_expense if canteen_expense else 0.0,
                    'net_amount': net_amount if net_amount else 0.0,

                }

                lines.append(res)
            if lines:
                return lines
            else:
                return []
        elif target_move == True:


            query1 = '''
            select dd.id,
                (dd.employee_name) as employee_name,
                (dd.designation) as designation,
                (dd.department) as department,
                (dd.basic_salary) as basic_salary,
                (dd.no_of_days) as no_of_days,
                (dd.working_days) as working_days,
                (dd.no_of_days)-(dd.working_days) as leave_days,
                (dd.basic_salary/dd.no_of_days)*(dd.working_days) as salary_for_the_month,
                (dd.less_tds) as less_tds,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))-(dd.less_tds) as salary_payable,
                dd.other_deduction as other_deduction,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))*0.75/100 as esi_employee_deduction,
                ((dd.basic_salary/dd.no_of_days)*(dd.working_days))*3.25/100 as esi_employer_contribution,
                dd.canteen_expense as canteen_expense,
                dd.travelling_expense as travelling_expense,


                dd.net_amount as net_amount



                        from

                        ((select hre.id as id,
                        hre.name as employee_name,
                                max(hrj.name) as designation,
                                max(hp.name) as department,
                                 sum(case when hrpl.name='Basic Salary' then hrpl.total else 0 end) as basic_salary,
                                 date_part('days',date_trunc('month',to_date(%s,'YYYY-MM-DD'))+'1 MONTH'::INTERVAL-
                                         date_trunc('month',to_date(%s,'YYYY-MM-DD'))) as no_of_days,
                          sum(case when hrpl.code ~~* 'TDS%%' then hrpl.total else 0 end) as less_tds,
                          sum(case when hrpl.code='NET' then hrpl.total else 0 end) as net_amount,
                           sum(case when hrpl.code='Can Ex' then hrpl.total else 0 end) as canteen_expense,
                          max(hrj.name) job



                                from hr_payslip_line as hrpl
                            left join hr_payslip as hrp on hrp.id=hrpl.slip_id
                            left join hr_employee as hre on hre.id=hrp.employee_id
                            left join hr_department as hp on hp.id=hre.department_id
                            left join hr_job as hrj on hrj.id=hre.job_id

                            where to_char(date_trunc('day',hrp.date_from),'YYYY-MM-DD')::date between %s and %s
                          and hrp.company_id=%s
                          and (hrj.name not in ('Health Care Assistance') OR hrj.name is null)
                          and hrp.state in ('verify','done')

                            group by hre.id) as a

                            left join
                            (select sum(hw.number_of_days) as working_days,h.employee_id as employee_id from hr_payslip as h
                            left join hr_payslip_worked_days as hw on h.id=hw.payslip_id
                            where to_char(date_trunc('day',h.date_from),'YYYY-MM-DD')::date between %s and %s
                             and h.company_id=%s
                             and h.state in ('verify','done')
                            group by h.employee_id)as b on a.id=b.employee_id

                         left join
                         (select hl.employee_id as em_id,
                          sum(case when hl.code !~~* 'TDS%%' and hl.code<>'Can Ex' and hc.name='Deduction'  then hl.total else 0 end) as other_deduction
                         from hr_payslip_line as hl
                          left join hr_payslip as hp on hp.id=hl.slip_id
                          left join hr_salary_rule_category as hc on hc.id=hl.category_id
                          where to_char(date_trunc('day',hp.date_from),'YYYY-MM-DD')::date between %s and %s
                          and hp.company_id=%s
                             and hp.state in ('verify','done')

                          group by hl.employee_id
                         )as c on a.id=c.em_id

                         left join
                         (select expense.employee_id as emp_id,
                          sum(case when pt.name='Travelling Expense' then expense.total_amount else 0 end) as travelling_expense
                            from hr_expense as expense
                          left join hr_employee as employee on employee.id=expense.employee_id
                          left join product_product as p on p.id=expense.product_id
                          left join product_template as pt on pt.id=p.product_tmpl_id
                          where to_char(date_trunc('day',expense.date),'YYYY-MM-DD')::date between %s and %s
                          and pt.name='Travelling Expense'
                          and expense.company_id=%s

                          group by expense.employee_id
                         )as d on a.id=d.emp_id

                        )dd
                                                           '''


            self.env.cr.execute(query1,(
                date_to, date_to,
                date_from, date_to, company_id,
                date_from, date_to, company_id,
                date_from, date_to, company_id,
                date_from, date_to, company_id,))

            for row in self._cr.dictfetchall():
                sl += 1

                employee_name = row['employee_name'] if row['employee_name'] else " "
                designation = row['designation'] if row['designation'] else " "
                department = row['department'] if row['department'] else " "
                basic_salary = row['basic_salary'] if row['basic_salary'] else 0.0
                no_of_days = row['no_of_days'] if row['no_of_days'] else 0.0
                working_days = row['working_days'] if row['working_days'] else 0.0
                # total_amount = row['total_amount'] if row['total_amount'] else 0
                # sale_new_date = datetime.strptime(str(saledate), '%Y-%m-%d').date().strftime('%d-%m-%Y')
                leave_days = row['leave_days'] if row['leave_days'] else 0.0
                salary_for_the_month = row['salary_for_the_month'] if row['salary_for_the_month'] else 0.0
                less_tds = row['less_tds'] if row['less_tds'] else 0.0
                salary_payable = row['salary_payable'] if row['salary_payable'] else 0.0
                other_deduction = row['other_deduction'] if row['other_deduction'] else 0.0
                esi_employee_deduction = row['esi_employee_deduction'] if row['esi_employee_deduction'] else 0.0
                esi_employer_contribution = row['esi_employer_contribution'] if row['esi_employer_contribution'] else 0.0
                canteen_expense = row['canteen_expense'] if row['canteen_expense'] else 0.0
                net_amount = row['net_amount'] if row['net_amount'] else 0.0
                travelling_expense = row['travelling_expense'] if row['travelling_expense'] else 0.0
                res = {
                    'sl_no': sl,
                    'employee_name': employee_name if employee_name else " ",
                    'designation': designation if designation else " ",
                    'department': department if department else " ",
                    'basic_salary': basic_salary if basic_salary else 0.0,
                    'no_of_days': no_of_days if no_of_days else 0.0,
                    'working_days': working_days if working_days else 0.0,
                    'leave_days': leave_days if leave_days else 0.0,
                    'salary_for_the_month': salary_for_the_month if salary_for_the_month else 0.0,
                    'less_tds': less_tds if less_tds else 0.0,
                    'salary_payable': salary_payable if salary_payable else 0.0,
                    'other_deduction': other_deduction if other_deduction else 0.0,
                    'esi_employee_deduction': esi_employee_deduction if esi_employee_deduction else 0.0,
                    'esi_employer_contribution': esi_employer_contribution if esi_employer_contribution else 0.0,
                    'canteen_expense': canteen_expense if canteen_expense else 0.0,
                    'net_amount': net_amount if net_amount else 0.0,
                    'travelling_expense':travelling_expense if travelling_expense else 0.0

                }
                lines.append(res)

            if lines:
                return lines
            else:
                return []

    def generate_xlsx_report(self, workbook, data, lines):

        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        sheet = workbook.add_worksheet(_('Salary Statement Report'))
        sheet.set_landscape()
        sheet.set_default_row(25)
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        # sheet.set_column(0, 0, 14)
        # sheet.set_column(1, 1, 45)
        # sheet.set_column(2, 2, 22)
        # sheet.set_column(3, 5, 18)
        # sheet.set_column(4, 5, 20)


        # sheet.set_column(1, 1, 20)
        # sheet.set_column(2, 2, 25)
        # sheet.set_column(3, 3, 25)
        # sheet.set_column(4, 4, 20)
        # sheet.set_column(5, 5, 25)
        # sheet.set_column(6, 6, 20)
        # sheet.set_column(7, 7, 20)
        # sheet.set_column(8, 8, 20)
        # sheet.set_column(9, 9, 20)
        # sheet.set_column(10, 10, 20)
        # sheet.set_column(11, 11, 20)
        # sheet.set_column(12, 12, 20)
        # sheet.set_column(13, 13, 20)
        # sheet.set_column(14, 14, 20)
        # sheet.set_column(15, 15, 20)
        # sheet.set_column(16, 16, 20)
        # sheet.set_column(17, 17, 20)
        # sheet.set_column(18, 18, 20)
        # sheet.set_column(19, 19, 20)
        # sheet.set_column(20, 20, 20)
        # sheet.set_column(21, 21, 30)
        # sheet.set_column(22, 22, 20)
        # sheet.set_column(23, 23, 20)
        # sheet.set_column(24, 24, 20)

        company = self.env['res.company'].browse(data['form']['company_id'])

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        target_move = data['form']['target_move']
        if company.street:
            res = company.street
        else:
            res=""
        if company.street2:
            res2 = company.street2
        else:
            res2 = ""


        date_start = data['form']['date_from']
        date_end = data['form']['date_to']

        if date_start:

            date_object_date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        if date_end:
            date_object_date_end = datetime.strptime(date_end, '%Y-%m-%d').date()


        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14})
        font_size_8_center = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'center'})
        font_size_8_right = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'right'})
        font_size_8_left = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'left'})

        formattotal = workbook.add_format(
            {'bg_color': 'e2e8e8', 'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True,
             'align': 'right', 'bold': True})


        blue_mark2 = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14, 'bold': True,
             'color': 'ffffff', 'bg_color': '7b0b5b', 'align': 'center'})
        font_size_8blod = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14, 'bold': True, })

        blue_mark3 = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 18, 'bold': True,
             'color': 'ffffff', 'bg_color': '7b0b5b', 'align': 'center'})

        title_style = workbook.add_format({'font_size': 14, 'bold': True,
                                           'bg_color': '000000', 'color': 'ffffff',
                                           'bottom': 1, 'align': 'center'})
        account_style = workbook.add_format({'font_size': 14, 'bold': True,
                                           'bg_color': '929393', 'color': 'ffffff',
                                           'bottom': 1, 'align': 'left'})

        if target_move == False:

            sheet.set_column(1, 1, 20)
            sheet.set_column(2, 2, 25)
            sheet.set_column(3, 3, 25)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 25)
            sheet.set_column(6, 6, 20)
            sheet.set_column(7, 7, 20)
            sheet.set_column(8, 8, 20)
            sheet.set_column(9, 9, 20)
            sheet.set_column(10, 10, 20)
            sheet.set_column(11, 11, 20)
            sheet.set_column(12, 12, 20)
            sheet.set_column(13, 13, 20)
            sheet.set_column(14, 14, 20)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 20)
            sheet.set_column(17, 17, 20)
            sheet.set_column(18, 18, 20)
            sheet.set_column(19, 19, 20)
            sheet.set_column(20, 20, 20)
            sheet.set_column(21, 21, 30)
            sheet.set_column(22, 22, 20)
            sheet.set_column(23, 23, 20)
            sheet.set_column(24, 24, 20)

            date_start = data['form']['date_from']
            date_end = data['form']['date_to']


            if date_end:
                date_month = datetime.strptime(date_end, '%Y-%m-%d').date().strftime('%B')
                date_year = datetime.strptime(date_end, '%Y-%m-%d').date().strftime('%Y')
            else:
                date_month = ""
                date_year = ""



            sheet.merge_range('A1:Q1', company.name, blue_mark3)
            # sheet.merge_range('A2:P2', res+" ," + res2, blue_mark2)
            sheet.merge_range('A2:Q2', "SALARY STATEMENT FOR THE MONTH OF "+date_month+" "+date_year, blue_mark2)

            self.model = self.env.context.get('active_model')
            docs = self.env[self.model].browse(self.env.context.get('active_ids', []))


            if date_start and date_end:

                sheet.merge_range('A5:Q5', "Date : "+date_object_date_start.strftime('%d-%m-%Y')+ " to "+date_object_date_end.strftime('%d-%m-%Y'), font_size_8blod)
            elif date_start:
                sheet.merge_range('A5:Q5', "Date : " + date_object_date_start.strftime('%d-%m-%Y') ,
                                  font_size_8blod)

            sheet.write('A6', "SL.NO.", title_style)

            sheet.write('B6', "NAME OF THE EMPLOYEE", title_style)
            sheet.write('C6', "DESIGNATION", title_style)
            sheet.write('D6', "DEPARTMENT", title_style)
            sheet.write('E6', "BASIC SALARY", title_style)
            sheet.write('F6', "NO OF DAYS FOR THIS MONTH", title_style)
            sheet.write('G6', "NO OF LEAVE DAYS", title_style)
            sheet.write('H6', "WORKING DAYS", title_style)
            sheet.write('I6', "SALARY FOR THE MONTH", title_style)

            sheet.write('J6', "LESS TDS", title_style)
            sheet.write('K6', "SALARY PAYABLE", title_style)
            sheet.write('L6', "OTHER DEDUCTIONS", title_style)
            sheet.write('M6', "ESI Employee Deduction(0.75%)", title_style)
            sheet.write('N6', "ESI Employer Contribution(3.25%)", title_style)
            sheet.write('O6', "Canteen Exp.", title_style)
            sheet.write('P6', "NET AMOUNT PAYABLE", title_style)
            sheet.write('Q6', "REMARKS", title_style)

            linw_row = 6
            line_column = 0


            for line in self.get_sale(data):
                sheet.write(linw_row, line_column, line['sl_no'], font_size_8_center)
                sheet.write(linw_row, line_column + 1, line['employee_name'], font_size_8_left)

                sheet.write(linw_row, line_column + 2, line['designation'], font_size_8_left)
                sheet.write(linw_row, line_column + 3, line['department'], font_size_8_left)
                sheet.write(linw_row, line_column + 4, '{0:.2f}'.format(float(line['basic_salary'])), font_size_8_right)
                sheet.write(linw_row, line_column + 5, '{0:.2f}'.format(float(line['no_of_days'])), font_size_8_right)

                sheet.write(linw_row, line_column + 6, '{0:.2f}'.format(float(line['leave_days'])), font_size_8_right)
                sheet.write(linw_row, line_column + 7, '{0:.2f}'.format(float(line['working_days'])), font_size_8_right)
                sheet.write(linw_row, line_column + 8, '{0:.2f}'.format(float(line['salary_for_the_month'])),font_size_8_right)
                sheet.write(linw_row, line_column + 9, '{0:.2f}'.format(float(line['less_tds'])), font_size_8_right)
                sheet.write(linw_row, line_column + 10, '{0:.2f}'.format(float(line['salary_payable'])),font_size_8_right)
                sheet.write(linw_row, line_column + 11, '{0:.2f}'.format(float(line['other_deduction'])),font_size_8_right)

                sheet.write(linw_row, line_column + 12, '{0:.2f}'.format(float(line['esi_deduction'])), font_size_8_right)


                # sheet.write(linw_row, line_column + 12, '{0:.2f}'.format(float(line['esi_employee_deduction'])), font_size_8_right)

                sheet.write(linw_row, line_column + 13, '{0:.2f}'.format(float(line['esi_employer_contribution'])),font_size_8_right)
                sheet.write(linw_row, line_column + 14, '{0:.2f}'.format(float(line['canteen_expense'])),font_size_8_right)
                sheet.write(linw_row, line_column + 15, '{0:.2f}'.format(float(line['net_amount'])), font_size_8_right)
                sheet.write(linw_row, line_column + 16, "",font_size_8_right)


                linw_row = linw_row + 1
                line_column = 0

            line_column = 0

            sheet.merge_range(linw_row, 0, linw_row, 3, "TOTAL", font_size_8_left)

            total_cell_range = xl_range(6, 4, linw_row - 1, 4)
            total_cell_range5 = xl_range(6, 5, linw_row - 1, 5)
            total_cell_range6 = xl_range(6, 6, linw_row - 1, 6)
            total_cell_range7 = xl_range(6, 7, linw_row - 1, 7)
            total_cell_range8 = xl_range(6, 8, linw_row - 1, 8)
            total_cell_range9 = xl_range(6, 9, linw_row - 1, 9)
            total_cell_range10 = xl_range(6, 10, linw_row - 1, 10)
            total_cell_range11 = xl_range(6, 11, linw_row - 1, 11)
            total_cell_range12 = xl_range(6, 12, linw_row - 1, 12)
            total_cell_range13 = xl_range(6, 13, linw_row - 1, 13)
            total_cell_range14 = xl_range(6, 14, linw_row - 1, 14)
            total_cell_range15 = xl_range(6, 15, linw_row - 1, 15)

            sheet.write_formula(linw_row, 4, '=SUM(' + total_cell_range + ')', font_size_8_right)
            sheet.write_formula(linw_row, 5, '=SUM(' + total_cell_range5 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 6, '=SUM(' + total_cell_range6+ ')', font_size_8_right)
            sheet.write_formula(linw_row, 7, '=SUM(' + total_cell_range7 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 8, '=SUM(' + total_cell_range8 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 9, '=SUM(' + total_cell_range9 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 10, '=SUM(' + total_cell_range10 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 11, '=SUM(' + total_cell_range11 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 12, '=SUM(' + total_cell_range12 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 13, '=SUM(' + total_cell_range13 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 14, '=SUM(' + total_cell_range14 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 15, '=SUM(' + total_cell_range15 + ')', font_size_8_right)
        elif target_move == True:

            sheet.set_column(1, 1, 25)
            sheet.set_column(2, 2, 25)
            sheet.set_column(3, 3, 25)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 25)
            sheet.set_column(6, 6, 20)
            sheet.set_column(7, 7, 20)
            sheet.set_column(8, 8, 20)
            sheet.set_column(9, 9, 20)
            sheet.set_column(10, 10, 20)
            sheet.set_column(11, 11, 20)
            sheet.set_column(12, 12, 20)
            sheet.set_column(13, 13, 20)
            sheet.set_column(14, 14, 20)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 20)
            sheet.set_column(17, 17, 20)
            sheet.set_column(18, 18, 20)
            sheet.set_column(19, 19, 20)
            sheet.set_column(20, 20, 20)
            sheet.set_column(21, 21, 30)
            sheet.set_column(22, 22, 20)
            sheet.set_column(23, 23, 20)
            sheet.set_column(24, 24, 20)

            date_from = data['form']['date_from']
            date_to = data['form']['date_to']
            company_id = data['form']['company_id']
            target_move = data['form']['target_move']

            date_start = data['form']['date_from']
            date_end = data['form']['date_to']
            if date_start:
                date_object_date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            if date_end:
                date_object_date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
            if date_end:
                date_month = datetime.strptime(date_end, '%Y-%m-%d').date().strftime('%B')
                date_year = datetime.strptime(date_end, '%Y-%m-%d').date().strftime('%Y')
            else:
                date_month = ""
                date_year = ""

            sheet.merge_range('A1:P1', company.name, blue_mark3)

            # sheet.merge_range('A2:O2', res + " ," + res2, blue_mark2)
            sheet.merge_range('A2:P2', "Consultancy Charges Paid For The Month Of "+date_month+" "+date_year, blue_mark2)

            self.model = self.env.context.get('active_model')
            docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

            if date_start and date_end:

                sheet.merge_range('A5:P5', "Date : " + date_object_date_start.strftime(
                    '%d-%m-%Y') + " to " + date_object_date_end.strftime('%d-%m-%Y'), font_size_8blod)
            elif date_start:
                sheet.merge_range('A5:P5', "Date : " + date_object_date_start.strftime('%d-%m-%Y'),
                                  font_size_8blod)

            sheet.write('A6', "SL.NO.", title_style)

            sheet.write('B6', "NAME OF THE EMPLOYEE", title_style)
            sheet.write('C6', "DESIGNATION", title_style)
            sheet.write('D6', "DEPARTMENT", title_style)

            sheet.write('E6', "BASIC SALARY", title_style)
            sheet.write('F6', "NO OF DAYS FOR THIS MONTH", title_style)
            sheet.write('G6', "NO OF LEAVE DAYS", title_style)
            sheet.write('H6', "WORKING DAYS", title_style)
            sheet.write('I6', "SALARY FOR THE MONTH", title_style)
            sheet.write('J6', "LESS TDS", title_style)
            sheet.write('K6', "Travelling Exp", title_style)
            sheet.write('L6', "SALARY PAYABLE", title_style)
            sheet.write('M6', "OTHER DEDUCTIONS", title_style)
            sheet.write('N6', "Canteen Exp.", title_style)
            sheet.write('O6', "NET AMOUNT PAYABLE", title_style)
            sheet.write('P6', "REMARKS", title_style)

            linw_row = 6
            line_column = 0

            for line in self.get_sale(data):
                sheet.write(linw_row, line_column, line['sl_no'], font_size_8_center)
                sheet.write(linw_row, line_column + 1, line['employee_name'], font_size_8_left)

                sheet.write(linw_row, line_column + 2, line['designation'], font_size_8_left)
                sheet.write(linw_row, line_column + 3, line['department'], font_size_8_left)
                sheet.write(linw_row, line_column + 4, '{0:.2f}'.format(float(line['basic_salary'])), font_size_8_right)
                sheet.write(linw_row, line_column + 5, '{0:.2f}'.format(float(line['no_of_days'])), font_size_8_right)
                sheet.write(linw_row, line_column + 6, '{0:.2f}'.format(float(line['leave_days'])), font_size_8_right)
                sheet.write(linw_row, line_column + 7, '{0:.2f}'.format(float(line['working_days'])), font_size_8_right)
                sheet.write(linw_row, line_column + 8, '{0:.2f}'.format(float(line['salary_for_the_month'])),font_size_8_right)
                sheet.write(linw_row, line_column + 9, '{0:.2f}'.format(float(line['less_tds'])), font_size_8_right)
                sheet.write(linw_row, line_column + 10, '{0:.2f}'.format(float(line['travelling_expense'])),font_size_8_right)

                sheet.write(linw_row, line_column + 11, '{0:.2f}'.format(float(line['salary_payable'])),font_size_8_right)
                sheet.write(linw_row, line_column + 12, '{0:.2f}'.format(float(line['other_deduction'])),font_size_8_right)
                sheet.write(linw_row, line_column + 13, '{0:.2f}'.format(float(line['canteen_expense'])),font_size_8_right)
                sheet.write(linw_row, line_column + 14, '{0:.2f}'.format(float(line['net_amount'])), font_size_8_right)
                sheet.write(linw_row, line_column + 15, "", font_size_8_right)

                linw_row = linw_row + 1
                line_column = 0

            line_column = 0

            sheet.merge_range(linw_row, 0, linw_row, 3, "TOTAL", font_size_8_left)

            total_cell_range = xl_range(6, 4, linw_row - 1, 4)
            total_cell_range5 = xl_range(6, 5, linw_row - 1, 5)
            total_cell_range6 = xl_range(6, 6, linw_row - 1, 6)
            total_cell_range7 = xl_range(6, 7, linw_row - 1, 7)
            total_cell_range8 = xl_range(6, 8, linw_row - 1, 8)
            total_cell_range9 = xl_range(6, 9, linw_row - 1, 9)
            total_cell_range10 = xl_range(6, 10, linw_row - 1, 10)
            total_cell_range11 = xl_range(6, 11, linw_row - 1, 11)
            total_cell_range12 = xl_range(6, 12, linw_row - 1, 12)
            total_cell_range13 = xl_range(6, 13, linw_row - 1, 13)
            total_cell_range14 = xl_range(6, 14, linw_row - 1, 14)
            total_cell_range15 = xl_range(6, 15, linw_row - 1, 15)

            sheet.write_formula(linw_row, 4, '=SUM(' + total_cell_range + ')', font_size_8_right)
            sheet.write_formula(linw_row, 5, '=SUM(' + total_cell_range5 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 6, '=SUM(' + total_cell_range6 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 7, '=SUM(' + total_cell_range7 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 8, '=SUM(' + total_cell_range8 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 9, '=SUM(' + total_cell_range9 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 10, '=SUM(' + total_cell_range10 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 11, '=SUM(' + total_cell_range11 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 12, '=SUM(' + total_cell_range12 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 13, '=SUM(' + total_cell_range13 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 14, '=SUM(' + total_cell_range14 + ')', font_size_8_right)
            sheet.write_formula(linw_row, 15, '=SUM(' + total_cell_range15 + ')', font_size_8_right)





