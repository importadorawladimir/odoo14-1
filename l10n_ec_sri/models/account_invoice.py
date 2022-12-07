# -*- coding: utf-8 -*-
import unicodedata  # para normalizar el nombre
from collections import OrderedDict
from datetime import datetime

import pytz, logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import base64

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def get_detallesadicionales(self):
        """
        return: [(nombre,valor),(nombre,valor)]
        """
        return []

#
class AccountMove(models.Model):
    _inherit = 'account.move'

    #electronic_payment = fields.Selection(string=u"Pago Electrónico",
    #                                      selection=[('01', u'SIN UTILIZACIÓN DEL SISTEMA FINANCIERO'),
    #                                                 ('16', u'TARJETA DE DÉBITO'), ('17', u'DINERO ELECTRÓNICO'),
    #                                                 ('18', 'TARJETA PREPAGO'), ('19', u'TARJETA DE CRÉDITO'),
    #                                                 ('20', u'OTROS CON UTILIZACIÓN DEL SISTEMA FINANCIERO'),
    #                                                 ('21', u'ENDOSO DE TÍTULOS')], required=False, default="20")
    l10n_latam_document_auth = fields.Char(
        string='Autorizacion',
        required=False)

    def normalize_text(self, s, result='unicode'):
        remove = ['Mn', 'Po', 'Pc', 'Pd', 'Pf', 'Pi', 'Ps']
        res = ''.join((
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) not in remove
        ))

        return res

    def get_edi_docuemnt_auth(self):
        self.ensure_one()
        docs = self.edi_document_ids.filtered(lambda doc: doc.state == 'autorized')

        return len(docs) and docs[0] or False

    def get_edi_docuemnt_access_key(self):
        self.ensure_one()
        docs = self.edi_document_ids.filtered(lambda doc: doc.state != 'cancelled')

        return len(docs) and docs[0].claveacceso or False

    def normalize_date(self, date, fmt='dmy'):
        if fmt == 'dmy':
            return datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')

    def normalize_date_two(self, date, fmt='dmy'):
        if fmt == 'dmy':
            return date.strftime('%d/%m/%Y')

    def _get_custom_attachments(self):
        """
        Enviamos el documento electrónico de acuerdo al tipo
        para evitar errores en el envío.

        return: [('nombre_completo.ext','base64string')]
        """
        attachments = []
        if self.move_type == '	out_invoice':
            attachment_id = self.factura_electronica_id
        if self.move_type == 'out_refund':
            attachment_id = self.nota_credito_electronica_id

        if attachment_id:
            attachments.append(
                (attachment_id.xml_filename, attachment_id.xml_file)
            )
        return attachments


    def get_days(self, inv):
        date_format = '%Y-%m-%d'
        res = 0
        if inv:
            date_invoice = datetime.strptime(inv.date_invoice, date_format)
            date_due = datetime.strptime(inv.date_due, date_format)
            res = (date_due - date_invoice).days
        return res


    def get_email_template(self):
        if self.move_type == 'out_invoice':
            template = self.env.ref(
                'l10n_ec_sri.email_template_factura_electronica', False)
        elif self.move_type == 'in_invoice':
            template = self.env.ref(
                'l10n_ec_sri.email_template_retencion_electronica', False)
        elif self.move_type == 'out_refund':
            template = self.env.ref(
                'l10n_ec_sri.email_template_nota_de_credito_electronica', False)
        return template

    def _prepare_mail_context(self):
        template = self.get_email_template()
        attachment_ids = []
        doc = self.get_edi_docuemnt_auth()
        clave = doc and doc.claveacceso or self.name
        search = []

        search.append(eval("('res_model', '=', '" + self._name + "')"))
        search.append(eval("('res_id', '=', " + str(self.id) + ")"))
        search.append(eval("('name', 'in', ['" + clave + ".pdf','" + clave + ".xml'" + "])"))

        attachments = self.env['ir.attachment'].search(search)
        if len(attachments):
            for at in attachments:
                attachment_ids.append(at.id)
        else:
            if doc and (doc.xml_file or doc.ride_file):
                if doc.ride_file:
                    attrs = self.env['ir.attachment'].create({
                        'name': '{0}.pdf'.format(clave),
                        'datas': doc.ride_file,
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary'
                    })
                    attachment_ids.append(attrs)
                if doc.xml_file:
                    attrs = self.env['ir.attachment'].create({
                        'name': '{0}.xml'.format(clave),
                        'datas': doc.xml_file,
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary'
                    })
                    attachment_ids.append(attrs)
            else:

                pdf = \
                    self.env.ref('l10n_ec_sri.report_factura_electronica_id').sudo()._render_qweb_pdf(
                        [self.id])[
                        0]

                attrs = self.env['ir.attachment'].create({
                    'name': '{0}.pdf'.format(clave),
                    'datas': base64.b64encode(pdf),
                    'res_model': self._name,
                    'res_id': self.id,
                    'type': 'binary'
                })

                attachment_ids.append(attrs.id)


        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            default_attachment_ids=[(6, 0, attachment_ids)]
        )

        return ctx

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
           message loaded by default
        """

        if len(self.journal_id.edi_format_ids.filtered(lambda format: format.code == 'FESRI')):
            self.ensure_one()

            # Seleccionamos la plantilla de acuerdo al tipo.

            compose_form = self.env.ref(
                'mail.email_compose_message_wizard_form', False)


            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': self._prepare_mail_context(),
            }
        else:
            return super(AccountMove, self).action_invoice_sent()

    def emision_documentos_electronicos(self, aut, tipo):
        if aut.tipoem != 'E':
            return
        if tipo == 'f':
            if self.factura_electronica_id:
                if self.factura_electronica_id.state in ('RECIBIDA', 'AUTORIZADO'):
                    return
            self.button_send_factura_electronica()
        elif tipo == 'r':
            if self.retencion_electronica_id:
                if self.retencion_electronica_id.state in ('RECIBIDA', 'AUTORIZADO'):
                    return
            self.button_send_retencion_electronica()
        elif tipo == 'nc':
            if self.nota_credito_electronica_id:
                if self.nota_credito_electronica_id.state in ('RECIBIDA', 'AUTORIZADO'):
                    return
            self.button_send_nota_credito_electronica()
        return


    def get_infoadicional(self):
        """
        Información adicional para las notas de crédito
        y facturas.
        return: [(nombre,valor),(nombre,valor)]
        """
        info = []

        if self.partner_id:
            if self.partner_id.email:

                info.append(('Correo', self.partner_id.email))
            if self.partner_id.street:
                info.append(('Direccion', self.normalize(self.partner_id.street or '  ')))
            if self.partner_id.phone:
                info.append(('Telefono', self.normalize(self.partner_id.phone or '  ')))
        if self.narration:
            info.append(('Terminos y condiciones', self.normalize(self.narration)))
        return info



    def get_infotributaria_dict(self, ambiente_id, tipoemision, company,claveacceso):

        number = self.l10n_latam_document_number
        establecimiento = number[0:3]
        puntoemision = number[3:6]
        secuencial = number[6:15]

        infoTributaria = OrderedDict([
            ('ambiente', ambiente_id.ambiente),
            ('tipoEmision', tipoemision),
            ('razonSocial', self.normalize(company.name)),
            ('nombreComercial', self.normalize(company.company_registry or company.name)),
            ('ruc', len(company.vat) > 13 and company.vat[2:15] or company.vat),
            ('claveAcceso', claveacceso),
            ('codDoc', self.l10n_latam_document_type_id.electronic_code),
            ('estab', establecimiento),
            ('ptoEmi', puntoemision),
            ('secuencial', secuencial),
            ('dirMatriz', self.normalize(
                company.street or company.street + company.street2)),
        ])

        if company.agent_retention:
            number_resolution = company.ar_number_resolution
            number_resolution = number_resolution.split('-')

            number_resolution_int = int(number_resolution[len(number_resolution) - 1])
            if number_resolution_int > 0:
                agenteRetencion = number_resolution_int
                infoTributaria.update({'agenteRetencion': agenteRetencion})

        if company.regime_micro:
            infoTributaria.update({'regimenMicroempresas': u'CONTRIBUYENTE RÉGIMEN MICROEMPRESAS'})

        if company.regime_rimpe:
            infoTributaria.update({'contribuyenteRimpe': u'CONTRIBUYENTE RÉGIMEN RIMPE'})

        return infoTributaria

    def normalize(self, s):
        if not s:
            return
        return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

    def normalize_date(self, date):
        if not date:
            return
        try:
            res = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            res = datetime.strptime(
                date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        return res


    def get_propina(self):
        """
        Modificar con super
        :param self:
        :return: propina float
        """
        propina = 0.00
        return propina


    def get_factura_dict(self):
        """
        En caso de requerirse el tag infoAdicional se debe agregar con un super.

        :return:
         ambiente_id: en recordset,
         factura: OrderedDict,
         claveacceso: string,
         tipoemision: string,
        """
        ambiente_id = self.company_id.ambiente_id
        company = self.company_id
        #company_fiscal = company.partner_id.property_account_position_id
        move_type = self.move_type
        ruc = len(company.vat) > 13 and company.vat[2:15] or company.vat
        currency = self.journal_id.currency_id

        if ambiente_id.ambiente == '1':
            # Si el ambiente es de pruebas enviamos siempre la fecha actual.
            fechaemision = fields.Date.context_today(self)
        else:
            fechaemision = self.invoice_date


        tipoemision = '1'  # offline siempre es normal.
        partner = self.partner_id
        number = self.l10n_latam_document_number

        establecimiento = number[0:3]
        puntoemision = number[3:6]
        secuencial = number[6:15]

        de = self.env['account.edi.document']


        claveacceso = de.get_claveacceso(
            fechaemision,
            self.l10n_latam_document_type_id.electronic_code,
            ruc,
            company.ambiente_id,
            number[0:3],
            number[3:6],
            number[6:15],
            )

        infoTributaria = self.get_infotributaria_dict(ambiente_id, tipoemision, company,claveacceso)

        totalConImpuestos = OrderedDict([
            ('totalImpuesto', []),
        ])

        for tax in self.line_ids.filtered(lambda a: a.tax_line_id):
            if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('vat12', 'vat14', 'zero_vat', 'not_charged_vat', 'exempt_vat', 'ice','irbpnr'):
                totalConImpuestos['totalImpuesto'].append(OrderedDict([
                    ('codigo', tax.tax_line_id.tax_group_id.l10n_ec_electronic_code),
                    ('codigoPorcentaje', tax.tax_line_id.l10n_ec_electronic_code),
                    ('descuentoAdicional', '{:.2f}'.format(0)),  # TODO
                    ('baseImponible', '{:.2f}'.format(tax.tax_base_amount)),
                    ('tarifa', '{:.2f}'.format(tax.tax_line_id.amount)),
                    ('valor', '{:.2f}'.format(abs(tax.price_total))),
                ]))


        pagos = OrderedDict([
            ('pago', []),
        ])


        pagos['pago'].append(
            OrderedDict([
                ('formaPago', '20'),
                ('total', '{:.2f}'.format(self.amount_total)),
                ('plazo', 0),  # TODO
                ('unidadTiempo', 'dias'),  # TODO
            ]))

        detalles = OrderedDict([
            ('detalle', []),
        ])
        totalDescuento = 0.00
        other_vat_zero = {}
        for line in self.invoice_line_ids:
            impuestos = OrderedDict([
                ('impuesto', []),
            ])

            for tax in line.tax_ids:
                if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('vat12', 'vat14', 'zero_vat', 'not_charged_vat', 'exempt_vat', 'ice', 'irbpnr'):
                    # Compute 'price_subtotal'.
                    line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
                    subtotal = line.quantity * line_discount_price_unit

                    tax_amount = tax.compute_all(line_discount_price_unit,
                quantity=line.quantity, currency=currency, product=line.product_id, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
                    base = tax_amount['taxes'][0]['base']
                    amount = tax_amount['taxes'][0]['amount']

                    impuestos['impuesto'].append(
                        OrderedDict([
                            ('codigo', tax.tax_group_id.l10n_ec_electronic_code),
                            ('codigoPorcentaje', tax.l10n_ec_electronic_code),
                            ('tarifa', tax.amount),
                            ('baseImponible', '{:.2f}'.format(base)),
                            ('valor', '{:.2f}'.format(amount)),
                        ])
                    )

                    if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('zero_vat', 'not_charged_vat', 'exempt_vat'):
                        if not tax.tax_group_id.l10n_ec_type in other_vat_zero:
                            other_vat_zero[tax.tax_group_id.l10n_ec_type] = {
                                'codigo': tax.tax_group_id.l10n_ec_electronic_code,
                                'codigoPorcentaje': tax.l10n_ec_electronic_code,
                                'descuentoAdicional': '{:.2f}'.format(0),
                                'baseImponible': 0.00,
                                'tarifa': '{:.2f}'.format(0),
                                'valor': '{:.2f}'.format(0),
                            }
                        other_vat_zero[tax.tax_group_id.l10n_ec_type]['baseImponible'] +=base
            discount = 0.00
            if line.discount:
                discount = (line.price_unit * line.quantity) - line.price_subtotal
            detalle = OrderedDict([
                ('codigoPrincipal', line.product_id.default_code),
                ('codigoAuxiliar', line.product_id.barcode),
                ('descripcion', line.name and str(self.normalize(line.name)).replace("'","") or str(self.normalize(line.product_id.name)).replace("'","")),
                ('cantidad', '{:.6f}'.format(line.quantity)),
                ('precioUnitario', '{:.6f}'.format(line.price_unit)),
                ('descuento', '{:.2f}'.format(discount)),
                ('precioTotalSinImpuesto', '{:.2f}'.format(line.price_subtotal)),
            ])
            totalDescuento+=line.discount



            detalle.update(
                OrderedDict([
                    ('impuestos', impuestos),
                ])
            )

            detalles['detalle'].append(detalle)

        for key, total_tax in other_vat_zero.items():
            totalConImpuestos['totalImpuesto'].append(OrderedDict([
                ('codigo', total_tax.get('codigo')),
                ('codigoPorcentaje', total_tax.get('codigoPorcentaje')),
                ('descuentoAdicional', total_tax.get('descuentoAdicional')),  # TODO
                ('baseImponible', '{:.2f}'.format(total_tax.get('baseImponible', 0.00))),
                ('tarifa', total_tax.get('tarifa')),
                ('valor', total_tax.get('valor')),
            ]))
        tipoIdentificacionComprador = partner.l10n_latam_identification_type_id.electronic_code or '05'

        if partner.vat == "9999999999999":
            tipoIdentificacionComprador = "07"

        infoFactura = OrderedDict([
            ('fechaEmision', self.normalize_date_two(fechaemision)),
            ('dirEstablecimiento', self.journal_id.dir_establecimiento and self.normalize(self.journal_id.dir_establecimiento) or self.normalize(company.street)),
            ('contribuyenteEspecial', company.is_special_taxpayer_number and company.special_taxpayer_number or '000'),
            ('obligadoContabilidad', company.takes_accounting and 'SI' or 'NO'),
            ('tipoIdentificacionComprador', tipoIdentificacionComprador),
            ('guiaRemision', '000-000-000000000'),  # TODO
            ('razonSocialComprador', self.normalize(partner.name)),
            ('identificacionComprador', partner.vat),
            ('direccionComprador', partner.street),
            ('totalSinImpuestos', '{:.2f}'.format(self.amount_untaxed)),
            ('totalDescuento', '{:.2f}'.format(totalDescuento)),
            ('totalConImpuestos', totalConImpuestos),
            ('propina', '{:.2f}'.format(self.get_propina())),
            ('importeTotal', '{:.2f}'.format(self.amount_total)),
            ('moneda', 'DOLAR'),
            ('pagos', pagos),
        ])

        if infoFactura.get('contribuyenteEspecial','000') == '000':
            infoFactura.pop('contribuyenteEspecial')

        factura_dict = OrderedDict([
                ('factura', OrderedDict([
                    ('@id', 'comprobante'),
                    ('@version', '1.1.0'),
                    ('infoTributaria', infoTributaria),
                    ('infoFactura', infoFactura),
                    ('detalles', detalles),
                ]),
                )
            ])

        camposAdicionales = self.get_infoadicional()
        if camposAdicionales:
            infoAdicional = OrderedDict([
                ('campoAdicional', []),
            ])
            for c in camposAdicionales:
                infoAdicional['campoAdicional'].append(OrderedDict([
                    ('@nombre', c[0]),
                    ('#text', c[1]),
                ]))

            factura_dict.get('factura').update(OrderedDict([
                ('infoAdicional', infoAdicional),
            ])
            )

        return ambiente_id,factura_dict, claveacceso, tipoemision

    def get_nota_credito_dict(self):
        """
        En caso de requerirse el tag infoAdicional se debe agregar con un super.

        :return:
         ambiente_id: en recordset,
         factura: OrderedDict,
         claveacceso: string,
         tipoemision: string,
        """
        ambiente_id = self.company_id.ambiente_id
        company = self.company_id
        #company_fiscal = company.partner_id.property_account_position_id
        move_type = self.move_type
        ruc = len(company.vat) > 13 and company.vat[2:15] or company.vat
        currency = self.journal_id.currency_id

        if ambiente_id.ambiente == '1':
            # Si el ambiente es de pruebas enviamos siempre la fecha actual.
            fechaemision = fields.Date.context_today(self)
        else:
            fechaemision = self.invoice_date


        tipoemision = '1'  # offline siempre es normal.
        partner = self.partner_id
        number = self.l10n_latam_document_number

        establecimiento = number[0:3]
        puntoemision = number[3:6]
        secuencial = number[6:15]

        de = self.env['account.edi.document']


        claveacceso = de.get_claveacceso(
            fechaemision,
            self.l10n_latam_document_type_id.electronic_code,
            ruc,
            company.ambiente_id,
            establecimiento,
            puntoemision,
            secuencial,
            )

        infoTributaria = self.get_infotributaria_dict(ambiente_id, tipoemision, company,claveacceso)

        totalConImpuestos = OrderedDict([
            ('totalImpuesto', []),
        ])

        for tax in self.line_ids.filtered(lambda a: a.tax_line_id):
            if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('vat12', 'vat14', 'zero_vat', 'not_charged_vat', 'exempt_vat', 'ice','irbpnr'):
                totalConImpuestos['totalImpuesto'].append(OrderedDict([
                    ('codigo', tax.tax_line_id.tax_group_id.l10n_ec_electronic_code),
                    ('codigoPorcentaje', tax.tax_line_id.l10n_ec_electronic_code),
                    ('baseImponible', '{:.2f}'.format(tax.tax_base_amount)),
                    #('tarifa', '{:.2f}'.format(tax.tax_line_id.amount)),
                    ('valor', '{:.2f}'.format(abs(tax.price_total))),
                ]))


        detalles = OrderedDict([
            ('detalle', []),
        ])
        totalDescuento = 0.00
        other_vat_zero = {}
        for line in self.invoice_line_ids:
            impuestos = OrderedDict([
                ('impuesto', []),
            ])

            for tax in line.tax_ids:
                if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('vat12', 'vat14', 'zero_vat', 'not_charged_vat', 'exempt_vat', 'ice', 'irbpnr'):
                    # Compute 'price_subtotal'.
                    line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
                    subtotal = line.quantity * line_discount_price_unit

                    tax_amount = tax.compute_all(line_discount_price_unit,
                quantity=line.quantity, currency=currency, product=line.product_id, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
                    base = tax_amount['taxes'][0]['base']
                    amount = tax_amount['taxes'][0]['amount']

                    impuestos['impuesto'].append(
                        OrderedDict([
                            ('codigo', tax.tax_group_id.l10n_ec_electronic_code),
                            ('codigoPorcentaje', tax.l10n_ec_electronic_code),
                            ('tarifa', tax.amount),
                            ('baseImponible', '{:.2f}'.format(base)),
                            ('valor', '{:.2f}'.format(amount)),
                        ])
                    )

                    if tax.tax_group_id and tax.tax_group_id.l10n_ec_type in ('zero_vat', 'not_charged_vat', 'exempt_vat'):
                        if not tax.tax_group_id.l10n_ec_type in other_vat_zero:
                            other_vat_zero[tax.tax_group_id.l10n_ec_type] = {
                                'codigo': tax.tax_group_id.l10n_ec_electronic_code,
                                'codigoPorcentaje': tax.l10n_ec_electronic_code,
                                'tarifa': '{:.2f}'.format(0),
                                'baseImponible': 0.00,
                                'valor': '{:.2f}'.format(0),
                            }
                        other_vat_zero[tax.tax_group_id.l10n_ec_type]['baseImponible'] +=base

            detalle = OrderedDict([
                ('codigoInterno', line.product_id.default_code),
                ('descripcion', str(self.normalize(line.name)).replace("'","")),
                ('cantidad', '{:.6f}'.format(line.quantity)),
                ('precioUnitario', '{:.6f}'.format(line.price_unit)),
                ('descuento', '{:.2f}'.format(line.discount)),
                ('precioTotalSinImpuesto', '{:.2f}'.format(line.price_subtotal)),
            ])
            totalDescuento+=line.discount



            detalle.update(
                OrderedDict([
                    ('impuestos', impuestos),
                ])
            )

            detalles['detalle'].append(detalle)

        for key, total_tax in other_vat_zero.items():
            totalConImpuestos['totalImpuesto'].append(OrderedDict([
                ('codigo', total_tax.get('codigo')),
                ('codigoPorcentaje', total_tax.get('codigoPorcentaje')),
                ('baseImponible', '{:.2f}'.format(total_tax.get('baseImponible', 0.00))),
                ('valor', total_tax.get('valor')),
            ]))
        tipoIdentificacionComprador = partner.l10n_latam_identification_type_id.electronic_code or '05'

        if partner.vat == "9999999999999":
            tipoIdentificacionComprador = "07"

        numDocModificado = "000-000-000000000"
        codDocModificado = "01"
        fechaEmisionDocSustento = fechaemision
        if self.l10n_latam_document_sustento_id:
            docSustento = self.l10n_latam_document_sustento_id
            _number = docSustento.l10n_latam_document_number
            numDocModificado = "%s-%s-%s" % (_number[0:3],_number[3:6],_number[6:15])
            codDocModificado = docSustento.l10n_latam_document_type_id.electronic_code
            if ambiente_id.ambiente == '1':
                # Si el ambiente es de pruebas enviamos siempre la fecha actual.
                fechaEmisionDocSustento = fields.Date.context_today(self)
            else:
                fechaEmisionDocSustento = docSustento.invoice_date


        infoNotaCredito = OrderedDict([
            ('fechaEmision', self.normalize_date_two(fechaemision)),
            ('dirEstablecimiento', self.journal_id.dir_establecimiento and self.normalize(self.journal_id.dir_establecimiento) or self.normalize(company.street)),
            ('tipoIdentificacionComprador', tipoIdentificacionComprador),
            ('razonSocialComprador', self.normalize(partner.name)),
            ('identificacionComprador', partner.vat),
            ('obligadoContabilidad', company.takes_accounting and 'SI' or 'NO'),

            ('codDocModificado', codDocModificado),
            ('numDocModificado', numDocModificado),
            ('fechaEmisionDocSustento', self.normalize_date_two(fechaEmisionDocSustento)),

            ('totalSinImpuestos', '{:.2f}'.format(self.amount_untaxed)),
            ('valorModificacion', '{:.2f}'.format(self.amount_total)),
            ('moneda', 'DOLAR'),
            ('totalConImpuestos', totalConImpuestos),
            ('motivo', self.normalize(self.ref))
        ])

        #if infoFactura.get('contribuyenteEspecial','000') == '000':
        #    infoFactura.pop('contribuyenteEspecial')

        nota_credito_dict = OrderedDict([
                ('notaCredito', OrderedDict([
                    ('@id', 'comprobante'),
                    ('@version', '1.1.0'),
                    ('infoTributaria', infoTributaria),
                    ('infoNotaCredito', infoNotaCredito),
                    ('detalles', detalles),
                ]),
                )
            ])

        camposAdicionales = self.get_infoadicional()
        if camposAdicionales:
            infoAdicional = OrderedDict([
                ('campoAdicional', []),
            ])
            for c in camposAdicionales:
                infoAdicional['campoAdicional'].append(OrderedDict([
                    ('@nombre', c[0]),
                    ('#text', c[1]),
                ]))

            nota_credito_dict.get('notaCredito').update(OrderedDict([
                ('infoAdicional', infoAdicional),
            ])
            )

        return ambiente_id,nota_credito_dict, claveacceso, tipoemision


    def button_send_factura_electronica(self):
        ambiente_id, factura, claveacceso, tipoemision = self.get_factura_dict()

        de_obj = self.env['account.edi.document']
        reference = 'account.invoice,%s' % self.id

        vals = de_obj.get_documento_electronico_dict(
            ambiente_id, factura, claveacceso, tipoemision, reference
        )
        # La autorizacion de la factura es igual a la clave de acceso.
        self.autorizacion = claveacceso

        if self.factura_electronica_id:
            self.factura_electronica_id.write(vals)
        else:
            de = de_obj.create(vals)
            self.factura_electronica_id = de

        # Envía la nc y el archivo xml electónico a los correos de los clientes.
        # self.send_email_de()
        return True


    def get_retencion_dict(self):
        """
        En caso de requerirse el tag infoAdicional se debe agregar con un super.

        :return:
         ambiente_id: en recordset,
         comprobanteRetencion: OrderedDict,
         claveacceso: string,
         tipoemision: string,
        """
        ambiente_id = self.env.user.company_id.ambiente_id
        company = self.env.user.company_id
        company_fiscal = company.partner_id.property_account_position_id
        ruc = len(company.vat) > 13 and company.vat[2:15] or company.vat

        if ambiente_id.ambiente == '1':
            # Si el ambiente es de pruebas enviamos siempre la fecha actual.
            fechaemision = fields.Date.context_today(self)
        else:
            fechaemision = self.fechaemiret1

        autorizacion_id = self.r_autorizacion_id
        comprobante_id = self.r_comprobante_id
        comprobante = comprobante_id.electronic_code
        establecimiento = self.estabretencion1
        puntoemision = self.ptoemiretencion1
        tipoemision = '1'  # offline siempre es normal.
        secuencial = self.secretencion1.zfill(9)

        # Se refiere al documento del proveedor.
        numdocsustento = ''.join([
            (self.establecimiento).zfill(3),
            (self.puntoemision).zfill(3),
            (self.secuencial).zfill(9)
        ])

        partner = self.partner_id
        fiscal = partner.property_account_position_id
        de_obj = self.env['account.edi.document']
        claveacceso = de_obj.get_claveacceso(
            fechaemision, comprobante, ruc, ambiente_id,
            establecimiento, puntoemision, secuencial)

        infoTributaria = self.get_infotributaria_dict(
            ambiente_id, tipoemision, company, ruc,
            claveacceso, comprobante, establecimiento,
            puntoemision, secuencial)

        infoCompRetencion = OrderedDict([
            ('fechaEmision', self.normalize_date(fechaemision)),
            ('dirEstablecimiento', self.normalize(
                autorizacion_id.direstablecimiento or company.street + company.street2)),
            ('contribuyenteEspecial', company.contribuyenteespecial or '000'),
            ('obligadoContabilidad',
             company_fiscal.obligada_contabilidad and 'SI' or 'NO'),
            ('tipoIdentificacionSujetoRetenido',
             fiscal.identificacion_id.tpidcliente),
            ('razonSocialSujetoRetenido', self.normalize(partner.name)),
            ('identificacionSujetoRetenido', partner.vat),
            ('periodoFiscal', self.normalize_date(fechaemision)[3:10]),
        ])

        impuestos = OrderedDict([
            ('impuesto', []),
        ])

        for i in self.sri_tax_line_ids.filtered(lambda l: l.group in (
            'RetAir', 'RetBien10', 'RetServ20', 'RetServ50', 'RetBienes',
                'RetServicios', 'RetServ100')):
            impuestos['impuesto'].append(
                OrderedDict([
                    ('codigo', i.codigo),
                    ('codigoRetencion', i.codigoporcentaje),
                    ('baseImponible', i.base),
                    ('porcentajeRetener', i.porcentaje),
                    ('valorRetenido', '{:.2f}'.format(i.amount)),
                    ('codDocSustento', self.comprobante_id.code),
                    ('numDocSustento', numdocsustento),
                    ('fechaEmisionDocSustento',
                     self.normalize_date(self.date_invoice)),
                ]))

        retencion_dict = OrderedDict([
            ('comprobanteRetencion', OrderedDict([
                ('@id', 'comprobante'),
                ('@version', '1.0.0'),
                ('infoTributaria', infoTributaria),
                ('infoCompRetencion', infoCompRetencion),
                ('impuestos', impuestos),
            ]),
            )
        ])
        return ambiente_id, comprobante_id, retencion_dict, claveacceso, tipoemision


    def button_send_retencion_electronica(self):
        ambiente_id, comprobante_id, retencion_dict, claveacceso, tipoemision = self.get_retencion_dict()
        de_obj = self.env['account.edi.document']
        reference = 'account.invoice,%s' % self.id
        vals = de_obj.get_documento_electronico_dict(
            ambiente_id, comprobante_id, retencion_dict, claveacceso, tipoemision, reference
        )
        # La autorizacion de la retencion es igual a la clave de acceso.
        self.autretencion1 = claveacceso

        if self.retencion_electronica_id:
            self.retencion_electronica_id.write(vals)
        else:
            de = de_obj.create(vals)
            self.retencion_electronica_id = de

        # self.send_email_de()

        return True


    def send_de_backend(self):
        edoc = self.factura_electronica_id or self.retencion_electronica_id or self.nota_credito_electronica_id
        if edoc:
            try:
                edoc.receive_de_offline()
            except:
                edoc.send_de_backend()
            finally:
                if edoc.estado != 'DEVUELTA':
                    edoc.receive_de_offline()
        return True


    def send_email_de(self):


        self.ensure_one()
        template = self.get_email_template()

        template.with_context(self._prepare_mail_context()).send_mail(self.ids[0], force_send=True)

        for doc in self.edi_document_ids:
            doc.write({'mail_send': True})

        return True

    def button_send_nota_credito_electronica(self):
        ambiente_id, comprobante_id, nota_credito, claveacceso, tipoemision = self.get_nota_credito_dict()
        de_obj = self.env['account.edi.document']
        reference = 'account.invoice,%s' % self.id
        vals = de_obj.get_documento_electronico_dict(
            ambiente_id, comprobante_id, nota_credito, claveacceso, tipoemision, reference
        )
        # La autorizacion de la factura es igual a la clave de acceso.
        self.autorizacion = claveacceso

        if self.nota_credito_electronica_id:
            self.nota_credito_electronica_id.write(vals)
        else:
            de = de_obj.create(vals)
            self.nota_credito_electronica_id = de

        # Envía la nc y el archivo xml electónico a los correos de los clientes.
        # self.send_email_de()

        return True
