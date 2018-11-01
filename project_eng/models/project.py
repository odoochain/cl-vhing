# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sale_price = fields.Float(
        digits=dp.get_precision('Product Price')
    )
    cost_price = fields.Float(
        digits=dp.get_precision('Product Price')
    )
    product_id = fields.Many2one(
        'product.product'
    )


class Project(models.Model):
    _inherit = "project.project"

    purchase_count = fields.Integer(
        compute='_compute_purchase_count'
    )
    sales_count = fields.Integer(
        compute='_compute_sales_count'
    )
    work = fields.Char(

    )
    obs = fields.Char(

    )
    stage = fields.Integer(
        compute='_compute_stage',
        readonly=True
    )
    total_sales = fields.Float(
        compute='_compute_total_sales',
        readonly=True
    )
    percent_vh = fields.Float(
        compute='_compute_percent',
        readonly=True,
        string="VH %"
    )
    percent_ing = fields.Float(
        compute='_compute_percent',
        readonly=True,
        string="ING %"
    )

    @api.multi
    def _compute_stage(self):
        for proj in self:
            # obtener la etapa como
            # Sum( % avance tarea * $ tarea ) / Sum($ tarea)
            total_price = progress = 0
            for task in proj.tasks:
                total_price += task.sale_price
                progress += task.progress * task.sale_price
            proj.stage = progress / total_price

    @api.multi
    def _compute_percent(self):
        for proj in self:
            # calcular ing como SUM(compra) / SUM(venta) * 100

            sale_price = cost_price = 0.0
            for task in proj.tasks:
                cost_price += task.cost_price
                sale_price += task.sale_price

            proj.percent_ing = 100 * cost_price / sale_price if \
                sale_price != 0 else 0

            # calcular VH como 100 - ing
            proj.percent_vh = 100 - proj.percent_ing

    @api.multi
    def _compute_total_sales(self):
        for proj in self:
            analytic = proj.analytic_account_id
            domain = [('order_id.analytic_account_id.id', '=', analytic.id)]
            proj_sales = self.env['sale.order.line'].search(domain)
            total = 0.0
            for sale in proj_sales:
                total += sale.price_subtotal
            proj.total_sales = total

    @api.multi
    def _compute_purchase_count(self):
        for proj in self:
            analytic = proj.analytic_account_id
            _obj = self.env['purchase.order.line']
            domain = [('order_id.analytic_account_id.id', '=', analytic.id)]
            proj.purchase_count = _obj.search_count(domain)

    def _compute_sales_count(self):
        for proj in self:
            analytic = proj.analytic_account_id
            _obj = self.env['sale.order.line']
            domain = [('order_id.analytic_account_id.id', '=', analytic.id)]
            proj.sales_count = _obj.search_count(domain)

    @api.multi
    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.action_product_sale_list')
        analytic = self.analytic_account_id
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'domain': [('order_id.analytic_account_id.id', '=', analytic.id)],
        }

    @api.multi
    def action_view_purchases(self):
        self.ensure_one()
        analytic = self.analytic_account_id
        return {
            'name': _('Purchase Order Lines'),
            'help': False,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current',
            'res_model': 'purchase.order.line',
            'domain': [('order_id.analytic_account_id.id', '=', analytic.id)],
        }

    @api.model
    def create(self, vals):
        """ crear por defecto los estados de la lista de etapas.
        """
        res = super(Project, self).create(vals)
        tasks = self.env['project.task.type'].search([])
        for project in res:
            project.type_ids = tasks

        return res
