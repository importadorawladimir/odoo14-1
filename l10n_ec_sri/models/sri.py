# -*- coding: utf-8 -*-
import base64
import logging
import os
import io
import subprocess
import tempfile

import xml
from collections import OrderedDict
from lxml import etree as e
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config
_logger = logging.getLogger(__name__)
from suds.client import Client as susClient
from io import StringIO
try:
    import xmltodict
except ImportError:
    _logger.error(
        "The module xmltodict can't be loaded, try: pip install xmltodict")

try:
    from zeep import Client
except ImportError:
    _logger.warning("The module zeep can't be loaded, try: pip install zeep")

try:
    from barcode import generate
    from barcode.writer import ImageWriter
except ImportError:
    _logger.warning(
        "The module viivakoodi can't be loaded, try: pip install viivakoodi")


class SriFirma(models.Model):
    _name = 'l10n_ec_sri.firma'

    name = fields.Char(string='Descripción', required=True, )
    p12 = fields.Binary(string='Archivo de firma p12', required=True, )
    clave = fields.Char(string='Contraseña', required=True, )
    path = fields.Char(string='Ruta en disco', readonly=True, )
    valid_to = fields.Date(string='Fecha Vencimiento', )
    type_firm = fields.Selection(
        string='Tipo de Firma',
        selection=[('line', 'Firma en linea'),
                   ('bash', 'Firma en Bash'),
                   ('webservice', 'Firma Webservice'),],
        required=False, default='bash')


    def save_sign(self, p12):
        """
        Almacena la firma en disco
        :param p12: fields.Binary firma pfx
        :return: str() ruta del archivo
        """
        data_dir = config['data_dir']
        db = self.env.cr.dbname
        tmpp12 = tempfile.TemporaryFile()
        tmpp12 = tempfile.NamedTemporaryFile(suffix=".p12", prefix="firma_", dir=''.join(
            [data_dir, '/filestore/', db]), delete=False)  # TODO Cambiar la ruta
        tmpp12.write(base64.b64decode(p12))
        tmpp12.seek(0)
        return tmpp12.name

    @api.model
    def create(self, vals):
        if 'p12' in vals:
            vals['path'] = self.save_sign(vals['p12'])
        return super(SriFirma, self).create(vals)


    def write(self, vals):
        if 'p12' in vals:
            vals['path'] = self.save_sign(vals['p12'])
        return super(SriFirma, self).write(vals)


    def unlink(self):
        os.remove(self.path)
        return super(SriFirma, self).unlink()


class SriAmbiente(models.Model):
    _name = 'l10n_ec_sri.ambiente'

    name = fields.Char(string=u'Descripción', )
    ambiente = fields.Selection(
        [
            ('1', 'Pruebas'),
            ('2', 'Producción'),
        ],
        string='Ambiente', )
    recepcioncomprobantes = fields.Char(
        string='URL de recepción de comprobantes', )
    autorizacioncomprobantes = fields.Char(
        string='URL de autorización de comprobantes', )


class SriDocumentoElectronico(models.Model):
    _inherit = 'account.edi.document'


    def name_get(self):
        return [(documento.id, '%s %s' % (documento.claveacceso, documento.state)) for documento in self]

    @api.model
    def cron_generate_bash_xml(self, limit=1000):
        docs = self.search([('state', '=', 'to_send'),('claveacceso','!=',False),('move_id.move_type','=','out_invoice')], limit=limit)
        for rec in docs:
            move = rec.move_id
            ambiente_id, factura, claveacceso, tipoemision = move.get_factura_dict()
            reference = 'account.move,%s' % move.id
            self.get_documento_electronico_dict(ambiente_id, factura, rec.claveacceso, tipoemision, reference)

            rec.write({'state': 'sent'})

    @api.model
    def cron_generate_bash_access_key(self, limit=10000,ids=[]):
        if len(ids):
            docs = self.search([('move_id.id','in',ids)])
        else:
            docs = self.search([('state', 'in', ('to_send','sent','received')), ('claveacceso', '!=', False)], limit=limit)
        for rec in docs:
            move = rec.move_id

            company = move.company_id
            number = move.l10n_latam_document_number
            ruc = company.vat and company.vat[2:15] or "SINRUCCIA"

            claveacceso = rec.get_claveacceso(
                move.invoice_date,
                move.l10n_latam_document_type_id.electronic_code,
                ruc,
                company.ambiente_id,
                number[0:3],
                number[3:6],
                number[6:15],
            )

            if claveacceso and rec.claveacceso != claveacceso:
                rec.write({'claveacceso':claveacceso,'state': 'to_send'})

    @api.model
    def cron_send_bash_xml(self, limit=1000):
        docs = self.search([('state', '=', 'sent'),('claveacceso','!=',False),('claveacceso','!=','N/A')], limit=limit)
        receive = False
        for rec in docs:
            try:
                receive = rec.receive_de_offline(False)
            except Exception as ex:
                print(ex)

            try:
                if not receive:
                    rec.send_de_backend()
            except Exception as ex:
                print(ex)

    @api.model
    def cron_received_bash_auth(self, limit=1000):
        docs = self.search([('state', 'in', ['received','in_process'])], limit=limit)

        for rec in docs:
            try:
                rec.receive_de_offline()
            except Exception as ex:
                print(ex)

    @api.model
    def cron_send_email_electronic_document(self, limit=50):
        for rec in self.search([('edi_format_id.code', '=', 'FESRI'), ('mail_send', '=', False), ('state', '=', 'autorized')], limit=limit):
            rec.move_id.send_email_de()



    @api.model
    def create(self, vals):
        res = super(SriDocumentoElectronico, self).create(vals)
        if not res:
            return

        move = res.move_id

        company = move.company_id
        number = move.l10n_latam_document_number
        ruc = company.vat and company.vat[2:15] or "SINRUCCIA"
        claveacceso = self.get_claveacceso(
            move.invoice_date,
            move.l10n_latam_document_type_id.electronic_code,
            ruc,
            company.ambiente_id,
            number[0:3],
            number[3:6],
            number[6:15],
            )


        ambiente_id, factura, claveacceso, tipoemision = move.get_factura_dict()
        reference = 'account.move,%s' % self.id

        try:
            res.write(self.get_documento_electronico_dict(ambiente_id,factura,claveacceso, tipoemision, reference))
        except:
            pass

        return res


    def validate_xsd_schema(self, xml, xsd_path):
        """

        :param xml: xml codificado como utf-8
        :param xsd_path: /dir/archivo.xsd
        :return:
        """
        xsd_path = os.path.join(__file__, "../..", xsd_path)
        xsd_path = os.path.abspath(xsd_path)

        xsd = open(xsd_path)
        schema = e.parse(xsd)
        xsd = e.XMLSchema(schema)

        xml = e.XML(xml)

        try:
            xsd.assertValid(xml)
            return True
        except e.DocumentInvalid:
            return False


    def modulo11(self, clave):
        digitos = list(clave)
        nro = 6  # cantidad de digitos en cada segmento
        segmentos = [digitos[n:n + nro] for n in range(0, len(digitos), nro)]
        total = 0
        while segmentos:
            segmento = segmentos.pop()
            factor = 7  # numero inicial del mod11
            for s in segmento:
                total += int(s) * factor
                factor -= 1
        mod = 11 - (total % 11)
        if mod == 11:
            mod = 0
        elif mod == 10:
            mod = 1
        return mod


    def firma_xades_bes(self, xml, p12, clave,firma,claveacceso):
        """

        :param xml: cadena xml
        :param clave: clave en formato base64
        :param p12: archivo p12 en formato base64
        :return:
        """
        jar_path = os.path.join(__file__, "../../src/xadesBes/firma.jar")
        java_path = os.path.join(__file__, "../../src/lib/jre1.8.0_311/bin/java")

        jar_path = os.path.abspath(jar_path)
        java_path = os.path.abspath(java_path)

        cmd = [java_path, '-jar', jar_path, xml.decode().replace("\n",""), p12.decode(), clave.decode()]

        data_dir = config['data_dir']
        if firma.type_firm == 'line':
            try:
                subprocess.check_output(cmd)
                sp = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                res = sp.communicate()

                path_firm = os.path.join(data_dir, '/filestore/xml/firmado/')
                if not os.path.exists(path_firm):
                    os.makedirs(path_firm)

                with open(path_firm + "/" + claveacceso + ".xml", 'w') as f:
                    f.write(res[0])
                    f.close()

                return res[0]
            except subprocess.CalledProcessError as se:
                _logger.exception('FIRMA ELECTRONICA FALLIDA: %s' % se.returncode)
        elif firma.type_firm == 'bash':


            path_pending_firm = os.path.join(data_dir+'/filestore/xml/firmar/')

            if not os.path.exists(path_pending_firm):
                os.makedirs(path_pending_firm)

            file = os.path.join(path_pending_firm,claveacceso)
            with open(file, 'w') as f:
                cmd[3] = "'%s'" % cmd[3]
                f.write(' '.join(cmd))
                f.close()

            return False
        else:
            return False

    def send_de_backend(self):
        self.move_id.send_email_de()
        """
        Envía el documento electrónico desde el backend
        para evitar demoras en caso de que el SRI se encuentre
        fuera de línea.

        """

        xml = False
        ambiente_id = self.env.user.company_id.ambiente_id
        firma = self.env.user.company_id.firma_id
        if firma.type_firm == 'line':
            xml = base64.b64decode(self.xml_file)
        elif firma.type_firm == 'bash':
            data_dir = config['data_dir']
            path_firm = '%s/filestore/xml/firmado/' % data_dir
            clave = "%s.xml" % self.claveacceso
            xml_firm = os.path.join(path_firm,clave)

            if os.path.exists(xml_firm):
                with open(xml_firm) as info:
                    xml = info.read()
        else:
            return False

        if xml:
            envio = self.send_receipt(ambiente_id, xml)
            if envio:
                self.write({
                    'state': envio[0],
                    'error': envio[1] or '',
                })
                return True
            else:
                return False
        else:
            self.write({'state': 'to_send'})
        return False

    def send_de_offline(self, ambiente_id, xml):
        """
        :param ambiente_id: recordset del ambiente
        :param xml: documento xml en base 64
        :return: respuesta del SRI
        """
        return self.send_receipt(ambiente_id, xml)

        '''response = False
        client = Client(ambiente_id.recepcioncomprobantes)
        if client:
            response = client.service.validarComprobante(xml)
        return response'''

    def send_receipt(self, ambiente_id, xml):
        """
        Metodo que envia el XML al WS
        """

        buf = StringIO()
        buf.write(xml)
        buffer_xml = base64.encodestring(buf.getvalue().encode())

        #try:

        client = susClient(ambiente_id.recepcioncomprobantes)
        result = client.service.validarComprobante(buffer_xml.decode())

        errores = []
        #logging.info("<<RESULTADO SRI>>")
        #logging.info(result)

        if hasattr(result, "estado") and result.estado == 'RECIBIDA':
            return 'received' , ', '.join(errores)
        elif hasattr(result, "estado") and result.estado == 'EN PROCESO':
            return 'in_process', u"El documento se encuentra en estado 'EN PROCESO', este estado lo asigna el SRI cuando se demora en procesar un documento.\n Por favor intente más tarde"
        else:
            registrado = False
            if hasattr(result, "comprobantes"):
                for comp in result.comprobantes:
                    for m in comp[1][0].mensajes:
                        if int(m[1][0].identificador) == 43:
                            registrado = True
                            break
                        rs = [m[1][0].tipo, m[1][0].mensaje]
                        rs.append(getattr(m[1][0], 'informacionAdicional', ''))
                        errores.append(' '.join(rs))
                    if registrado:
                        break
                if registrado:
                    return 'received', ''

            return 'return', ', '.join(errores)
        #except ValueError:
        #    return False, ValueError.message

    def receive_de_offline(self,registre=True):
        ambiente_id = self.env.user.company_id.ambiente_id
        access_key = self.claveacceso
        messages = []
        client = Client(ambiente_id.autorizacioncomprobantes)
        result = client.service.autorizacionComprobante(access_key)

        if not hasattr(result, 'numeroComprobantes') and int(result.numeroComprobantes) == 0:
            return False

        if not hasattr(result.autorizaciones, 'autorizacion'):
            return False

        autorizacion = result.autorizaciones.autorizacion[0]
        mensajes = autorizacion.mensajes and autorizacion.mensajes.mensaje or []

        for m in mensajes:
            _smg = "[%s] - %s - (%s)" % (m.identificador, m.mensaje, m.informacionAdicional)
            messages.append(_smg)

        if autorizacion.estado == 'EN PROCESO':
            self.write({'state': 'in_process'})
            return True

        elif autorizacion.estado == 'AUTORIZADO':
            _autorizacion = OrderedDict([
                ('autorizacion', OrderedDict([
                    ('estado', autorizacion.estado),
                    ('numeroAutorizacion', autorizacion.numeroAutorizacion),
                    ('fechaAutorizacion', {'@class': 'fechaAutorizacion',
                                           '#text': str(autorizacion.fechaAutorizacion)}),
                    ('ambiente', autorizacion.ambiente),
                    ('comprobante', u'<![CDATA[{}]]>'.format(
                        autorizacion.comprobante)),
                ]))
            ])
            comprobante = xml.sax.saxutils.unescape(xmltodict.unparse(_autorizacion))


            self.write({
                'state': 'autorized',
                'error': False,
                'xml_file': base64.b64encode(comprobante.encode('utf-8')),
                'xml_filename': ''.join([access_key, '.xml']),
                'fechaautorizacion': fields.Datetime.to_string(autorizacion.fechaAutorizacion),
            })

            pdf = self.env.ref('l10n_ec_sri.report_factura_electronica_id').sudo()._render_qweb_pdf([self.move_id.id])[
                0]

            self.write({
                'ride_filename': ''.join([access_key, '.pdf']),
                'ride_file': base64.b64encode(pdf)
            })

            self.env['ir.attachment'].create({
                    'name': ''.join([access_key, '.pdf']),
                    'datas': base64.b64encode(pdf),
                    'res_model': 'account.move',
                    'res_id': self.move_id.id,
                    'type': 'binary'
                })
            self.env['ir.attachment'].create({
                    'name': ''.join([access_key, '.xml']),
                    'datas':  base64.b64encode(comprobante.encode('utf-8')),
                    'res_model': 'account.move',
                    'res_id': self.move_id.id,
                    'type': 'binary'
                })

            # Enviar correo si el documento es AUTORIZADO.
            '''try:
                sent = self.reference.send_email_de()
                # Si se envía, marcamos la línea como enviada.
                if sent:
                    line_obj = self.env['account.edi.document.queue.line']
                    line = line_obj.search([('edi_id', '=', self.id)], limit=1)
                    line.sent = True
            except:
                pass'''


            return True
        else:
            if registre ==True and len(messages):
                stateSave = self.state

                if autorizacion.estado == 'DEVUELTA':
                    stateSave = 'return'
                elif autorizacion.estado == 'RECHAZADA':
                    stateSave = 'REJECTED'
                elif autorizacion.estado == 'NO AUTORIZADO':
                    stateSave = 'unautorized'
                self.write({
                    'state': stateSave,
                    'error': " | ".join(messages)
                })

        return False



    def get_documento_electronico_dict(
            self, ambiente_id, documento, claveacceso, tipoemision, reference):
        # Generamos el xml en memoria.
        xml = xmltodict.unparse(documento, pretty=False)
        xml = xml.encode('utf8')

        # Validamos el esquema.
        xsd_path = 'src/esquemasXsd/Factura_V_1_1_0.xsd'
        self.validate_xsd_schema(xml, xsd_path)

        firma = self.env.user.company_id.firma_id
        clave = base64.b64encode(firma.clave.encode('ascii'))
        if not os.path.exists(firma.path):
            firma.write({
                'path': firma.save_sign(firma.p12),
            })
        p12 = base64.b64encode(firma.path.encode('ascii'))
        _xml = self.firma_xades_bes(xml,p12, clave, firma,claveacceso)
        filename = False
        if _xml:
            filename = ''.join([claveacceso, '.xml'])
            xml = _xml

        # Creamos el diccionario del documento electrónico.
        vals = {
            'xml_file': _xml and base64.b64encode(xml) or False,
            'xml_filename': filename,
            'error': '',
            'ambiente': ambiente_id.ambiente,
            'tipoemision': tipoemision,
            'claveacceso': claveacceso,
            'reference': reference
        }
        return vals


    def get_claveacceso(self, fecha, comprobante, ruc, ambiente_id,
                        establecimiento, puntoemision, secuencial):
        """

        :param fecha: fields.Date
        :param comprobante: código del tipo de comprobante en str zfill(2)
        :param ruc: de la empresa en str
        :param ambiente_id: recordset
        :param comprobante: str
        :param puntoemision: str
        :param secuencial: str
        :return:
        """
        #fecha = datetime.strptime(fecha, '%Y-%m-%d')
        data = [
            fecha.strftime('%d%m%Y'),
            str(comprobante),
            str(ruc),
            str(ambiente_id.ambiente),
            str(establecimiento).zfill(3),
            str(puntoemision).zfill(3),
            str(secuencial).zfill(9),
            str(secuencial[0:8]).zfill(8),
            '1',
        ]
        try:
            claveacceso = ''.join(data)
            claveacceso += str(self.modulo11(claveacceso))
        except:
            raise UserError(_(
                u"""
                La informacion para el comprobante eletronico esta incompleta:
                fecha = %s,
                comprobante = %s,
                ruc = %s,
                ambiente = %s,
                establecimiento = %s,
                puntoemision = %s,
                secuencial = %s,
                nro aleatorio = %s,
                Tipo de emisión = %s,
                """ % tuple(data)))
        return claveacceso


    def _get_reference_models(self):
        records = self.env['ir.model'].search(
            ['|', ('model', '=', 'account.move'), ('model', '=', 'stock.picking')])
        return [(record.model, record.name) for record in records] + [('', '')]

    reference = fields.Reference(
        string='Reference', selection='_get_reference_models')


    tipoemision = fields.Selection(
        [
            ('1', 'Emisión normal'),
            ('2', 'Emisión por indisponibilidad del sistema'),
        ],
        string='Tipo de emisión', )

    ambiente = fields.Selection([
        ('1', 'Pruebas'),
        ('2', 'Producción'),
    ], string='Ambiente', )

    @api.depends('claveacceso')
    def get_barcode_128(self):
        if self.claveacceso:
            file_data = io.StringIO()
            generate('code128', u'{}'.format(self.claveacceso),
                     writer=ImageWriter(), output=file_data)
            file_data.seek(0)
            self.barcode128 = base64.encodestring(file_data.read())

    claveacceso = fields.Char('Clave de acceso', )
    #barcode128 = fields.Binary('Barcode', compute=get_barcode_128)
    barcode128 = fields.Binary('Barcode')
    fechaautorizacion = fields.Datetime('Fecha y hora de autorización', )
    state = fields.Selection(
        selection_add=[
            ('received', 'RECIBIDA'),
            ('in_process', 'EN PROCESO'),
            ('return', 'DEVUELTA'),
            ('autorized', 'AUTORIZADO'),
            ('unautorized', 'NO AUTORIZADO'),
            ('rejected', 'RECHAZADA'),
        ]
    )

    xml_file = fields.Binary('Archivo XML', attachment=True, readonly=True, )
    xml_filename = fields.Char('Archivo XML', )

    ride_file = fields.Binary('RIDE', attachment=True, readonly=True, )
    ride_filename = fields.Char('RIDE', )

    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', 'Tipo de Documento', ondelete='cascade',
                                                  related="move_id.l10n_latam_document_type_id", readonly=True, store=True)

    mail_send = fields.Boolean(
        string='Correo Enviado?',
        required=False)



class SriDocumentosElectronicosQueue(models.Model):
    _name = 'account.edi.document.queue'
    _description = u'Documentos Electronicos queue'

    name = fields.Char(string='Name', )
    queue_line_ids = fields.One2many(
        'account.edi.document.queue.line',
        'queue_id',
        string='Cola de documentos electrónicos',
    )

    @api.model
    def process_de_queue(self, ids=None):
        queue = self.env['account.edi.document']
        pendientes = queue.filtered(
            lambda x: x.xml_file and x.state in ['to_send','received','in_process','autorized']
        )

        for p in pendientes:
            de = p
            if de.state == 'not_send':
                de.send_de_backend()

            if de.state in ('received', 'in_process'):
                de.receive_de_offline()

            if p.state == 'autorized':
                try:
                    sent = de.reference.send_email_de()
                    p.state = 'sent'
                except:
                   pass


class SriDocumentosElectronicosQueueLine(models.Model):
    _name = 'account.edi.document.queue.line'
    _description = 'Documentos Electronicos queue line'
    _order = 'create_date desc'

    sent = fields.Boolean(string='Sent', )
    state = fields.Selection(
        string='State', related="edi_id.state",
        store=True, )

    edi_id = fields.Many2one(
        'account.edi.document', string='Documento electronico', )
    reference = fields.Reference(
        related='edi_id.reference', string=_('Reference'))
    queue_id = fields.Many2one(
        'account.edi.document.queue', string='Queue', )
