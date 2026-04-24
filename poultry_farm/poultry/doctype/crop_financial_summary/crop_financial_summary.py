import frappe
from frappe.model.document import Document


class CropFinancialSummary(Document):

	def validate(self):
		self.calculate_derived_fields()

	def calculate_derived_fields(self):
		"""Recalculate cumulative cost and per-bird metrics when other_costs is edited."""
		total_feed = (
			(self.feed_cost_prestarter or 0)
			+ (self.feed_cost_c1 or 0)
			+ (self.feed_cost_c2 or 0)
			+ (self.feed_cost_c3 or 0)
			+ (self.feed_cost_finisher or 0)
		)
		self.total_feed_cost  = total_feed
		self.cumulative_cost  = (
			(self.chick_cost or 0)
			+ total_feed
			+ (self.mortality_loss_value or 0)
			+ (self.other_costs or 0)
		)
		self.gross_profit     = (self.total_revenue or 0) - (self.chick_cost or 0) - total_feed
		self.net_profit       = (self.total_revenue or 0) - self.cumulative_cost

		if self.total_revenue:
			self.profit_margin_pct = round(self.net_profit / self.total_revenue * 100, 2)

		if self.total_birds_slaughtered:
			self.cost_per_bird      = round(self.cumulative_cost / self.total_birds_slaughtered, 2)
			self.revenue_per_bird   = round((self.total_revenue or 0) / self.total_birds_slaughtered, 2)
			self.feed_cost_per_bird = round(total_feed / self.total_birds_slaughtered, 2)
