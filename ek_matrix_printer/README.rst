.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Impresor Direct Matrix Raw Proxy
===================================


Description
===========

* Impresion de documentos via proxy

* Impresion directa via RAW

* Impresion base64

* Impresion desde una vpn, cloud, servidor local , etc etc.

Installation
============

Instale el modulo directo.

Agregue un boton type=object con el atributo custom puede usar el valor "print" o el valor "print-ajax"

    <button string="Imprimir Matricial" icon="gtk-print" type="object" name="dummy" custom="print" class="print_matrix"/>

En caso de usar el valor print-ajax debe usar el instalador proxi inverso en el pc cliente

IMPORTANTE:
Para realizar nuevos reportes realizar herencia de este modulo.

Configuration
=============
1 Agregar en el codigo un campo type=Text con el nombre printer_data

2 Crear una plantilla via xml_data de tipo "email.template" en el cual configure el reporte a la medida.

3 Obtenga el reporte en base a la plantilla y con una funcion custom coloque el texto en el campo 'printer_data'

4 Imprimir el Reporte





Developer
=========


* Cristhian Luzon <@cristhian_70>


Maintainer
----------


This module is maintained by the Ekuasoft.

please visit http:/www.ekuasoft.com

