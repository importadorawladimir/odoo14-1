odoo.define('ek_matrix_printer.print_button', function(require){
"use strict";

var FormController = require('web.FormController');

var Session = require('web.Session');
FormController.include({

     htmlToElem: function(html) {
          let temp = document.createElement('template');
          html = html.trim(); // Never return a space text node as a result
          temp.innerHTML = html;
          return temp.content.firstChild;
        },

    _onButtonClicked: function(event){

        // en caso de querer imprimir todo, enviar contexto u otro parametro en custom=print'all'
        // recorrer todos los datos e imprimri, pero esto verificar si no se dana al momento de imprimir varias hojas

        if(event.data.attrs.custom == "print")
            {
                var printer_data = event.data.record.data.printer_data;
                if (!printer_data){
                        alert('No tiene datos para imprimir, porfavor actulice su informacion');
                        return;
                    }
                var raw = printer_data;
                /*
                IMPORTANTE: por la logica de estructura del core de Odoo creo una nueva ventana en la cual envio
                el RAW para realizar la impresion OntheFly
                */
                var base64=false;
                var newDiv = document.createElement("div");
                newDiv.appendChild(document.createTextNode(raw));
                newDiv.style.fontSize="10px";
                newDiv.style.fontFamily="monospace";
                if(base64){
                    newDiv.style.width="700px";
                    newDiv.style.wordWrap="break-word";
                }else newDiv.style.whiteSpace='pre';


                $('#frameek-pdf').remove();
                var $frm = $('<iframe style="display: none;">').attr({ id: 'frameek-pdf',  name: 'frameek-pdf' });
                $frm.appendTo(document.body).on( "load", function (responseText, textStatus, jqXHR) {
                window.frames['frameek-pdf'].document.write('<html><head><title>Impresor Ekuasoft by CL</title>');
                window.frames['frameek-pdf'].document.write("<style type='text/css' media='print'>@page{size:auto;margin:0mm; }body{background-color:#FFFFFF;border: solid 1px black;margin:0px;}</style></head><body>");
                window.frames['frameek-pdf'].document.write('</body></html>');
                window.frames['frameek-pdf'].document.body.appendChild(newDiv);
                window.frames['frameek-pdf'].focus();
                window.frames['frameek-pdf'].print();

                });
                console.log(printer_data);
                return;
            }
        else if(event.data.attrs.custom == "print-html")
            {
                var printer_data = event.data.record.data.printer_data;
                if (!printer_data){
                        alert('No tiene datos para imprimir, porfavor actulice su informacion');
                        return;
                    }
                var raw = printer_data;

                /*
                IMPORTANTE: por la logica de estructura del core de Odoo creo una nueva ventana en la cual envio
                el RAW para realizar la impresion OntheFly
                Agregar style for impresion
                let html="<style type='text/css' media='print'>@page{size:auto;margin:0mm; }body{background-color:#FFFFFF;border: solid 1px black;margin:0px;}</style>IMPRIMIR";
                */
	            $('<div>'+raw+'</div>').print({pageTitle:'Reportes'});
                return;

            }
        else if(event.data.attrs.custom == "print-frame")
            {
                var printer_data = event.data.record.data.printer_data;
                if (!printer_data){
                        alert('No tiene datos para imprimir, porfavor actulice su informacion');
                        return;
                    }
                var raw = printer_data;
                console.log('raw3');

                /*
                IMPORTANTE: por la logica de estructura del core de Odoo creo una nueva ventana en la cual envio
                el RAW para realizar la impresion OntheFly
                Agregar style for impresion
                let html="<style type='text/css' media='print'>@page{size:auto;margin:0mm; }body{background-color:#FFFFFF;border: solid 1px black;margin:0px;}</style>IMPRIMIR";
                */

                var html = ['<div><style type="text/css" media="print">@page{size:auto;margin:5mm; }body{background-color:#FFFFFF;border: solid 1px black;margin:0px;}</style>'];
                html.push(raw);
                html.push('</div>');
                var print_html = html.join('');
                var popupOrIframe = window.open('about:blank', 'printElementWindow', 'width=850,height=840,scrollbars=yes');
                var documentToWriteTo = popupOrIframe.document;
                documentToWriteTo.open();
                documentToWriteTo.write(print_html);
                popupOrIframe.focus();
                popupOrIframe.print();
                setTimeout(function(){documentToWriteTo.close();},10);

                return;
            }
        else if(event.data.attrs.custom === "print-ajax")
            {
                /*
                IMPRESION VIA AJAX POST RAW
                INSTALE EL CLIENTE DE IMPRESION CON UN PROXI INVERSO
                FUNCIONANDO COMO UN MICROSERVICIO
                */
                var printer_data = this.view.datarecord.printer_data;
                if (!printer_data){
                    alert('No tiene datos para imprimir, porfavor actulice su inf.');
                    return;
                }
                console.log(printer_data);
                var url = "http://localhost:8099/matrix/print";
                $.ajax({
                    type:"POST",
                    url: url,
                    data: {
                        printer_data: printer_data
                    },
                    success: function(data){
                        alert('Impresion Exitosa!');
                    },
                    error: function(data){
                        alert('Error de conexion, Revise su proxy que este activo.');
                        console.log(data);
                    }
                });

            }

        this._super(event);
    }
});
});