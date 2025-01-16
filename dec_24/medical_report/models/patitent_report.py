from odoo import models, fields, api
import base64

class MedicalExamination(models.Model):
    _name = 'medical.examination'
    _description = 'Medical Examination'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.today())

    height = fields.Float(string='Height (cm)')
    weight = fields.Float(string='Weight (kg)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    pulse = fields.Integer(string='Pulse (min)')
    bp_first = fields.Char(string='BP (First Reading)')
    bp_second = fields.Char(string='BP (Second Reading)')

    distant_vision_r = fields.Char('Distant Vision R')
    distant_vision_l = fields.Char('Distant Vision L')
    near_vision_r = fields.Char('Near Vision R')
    near_vision_l = fields.Char('Near Vision L')

    speech_right = fields.Selection([
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal')
    ], string='Right Ear')
    speech_left = fields.Selection([
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal')
    ], string='Left Ear')
    color_vision = fields.Selection([
        ('normal', 'Normal'),
        ('abnormal_safe', 'Abnormal safe'),
        ('abnormal_unsafe', 'Abnormal unsafe')
    ], string='Color Vision')

    general = fields.Text('General')
    eyes = fields.Text('Eyes')
    ent = fields.Text('ENT')
    oral_cavity = fields.Text('Oral Cavity')
    teeth = fields.Text('Teeth')
    lungs_chest = fields.Text('Lungs/Chest')
    cardiovascular = fields.Text('Cardiovascular')
    abdomen = fields.Text('Abdomen')
    hernial_orifices = fields.Text('Hernial Orifices')
    genitourinary = fields.Text('Genitourinary')
    musculoskeletal = fields.Text('Musculoskeletal')
    skin = fields.Text('Skin')
    blood_disorders = fields.Text('Blood Disorders')
    neurological = fields.Text('Neurological')
    endocrinological = fields.Text('Endocrinological')
    metabolic = fields.Text('Metabolic')
    cancer_tumor = fields.Text('Cancer/Tumor')
    infectious_dis = fields.Text('Infectious Dis.')

    chest_xray = fields.Text('Chest X-ray')
    ecg = fields.Text('ECG')
    spirometry = fields.Text('Spirometry')
    audiometry = fields.Text('Audiometry')
    vo2_max = fields.Text('VO2 max')

    lab_results = fields.Text('Lab Results')


    def generate_report(self):

        return self.env.ref('medical_report.action_medical_examination_report_pdf').report_action(self)
