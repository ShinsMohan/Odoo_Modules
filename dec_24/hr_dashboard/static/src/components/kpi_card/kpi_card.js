/** @odoo-module */

const { Component } = owl

export class KpiCard extends Component {}
export class KpiCardLarge extends Component {}
export class KpiCardMedium extends Component {}

KpiCard.template = 'hr_dashboard.KpiCard'
KpiCardLarge.template = 'hr_dashboard.KpiCardLarge'
KpiCardMedium.template = 'hr_dashboard.KpiCardMedium'