#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler
from models import Evento
from tokens import get_user_from_token
from util import parse_date
from google.appengine.ext import ndb
from facades.evento import crear_evento_tipo_usuario, evento_largo_clave, buscar_evento_categorias
# Expresiones regulares
import re
import flickr
from facades.excepcion import AgendamlgException
import util.json
from salida_eventos_json import eventos_json

class EventoHandler(BaseHandler):

    # Creacion de un evento, es una ruta que necesita autenticacion
    # Se recibe una lista de categorias, que son sus claves en version urlsafe
    def post(self):
        #Si el usuario no est autenticado se lanza excepcion
        _, usuario = get_user_from_token(self.request.headers.get('bearer'), raise_for_unauthenticated=True)

        evento_from_json = self.json_body()

        # Construir un clave parent adecuada para el evento, la cual es la id del usuario
        evento = Evento(parent=usuario.key)

        # Rellenar el evento

        evento.tipo = int(evento_from_json.get('tipo'))
        evento.nombre = evento_from_json.get('nombre', None)
        evento.descripcion = evento_from_json.get('descripcion', None)
        evento.fecha = parse_date(evento_from_json.get('fecha', None)).replace(tzinfo=None)
        evento.precio = evento_from_json.get('precio', None)
        evento.direccion = evento_from_json.get('direccion', None)
        # Si esta validado o no se gestiona en el el metodo de la fachada

        if (evento_from_json.get('latitud', None) is not None) and (evento_from_json.get('longitud', None) is not None):
            # Se ha proporcionado latitud y longitud para el evento a crear
            evento.coordenadas = ndb.GeoPt(evento_from_json['latitud'], evento_from_json['longitud'])
        else:
            evento.coordenadas = None

       # Rellenar las categorias del evento (lista de claves de categorias)
        evento.categorias = [ndb.Key(urlsafe=claveURLSafe) for claveURLSafe in evento_from_json.get('categorias', [])]
        # Gestionar datos de flickr
        modificarDatosFlickr(evento, evento_from_json.get('flickrUserID', None), evento_from_json.get('flickrAlbumID', None))

        # Persistir el evento
        crear_evento_tipo_usuario(usuario, evento)

        # Devolver evento recien creado completo
        self.response.write(util.json.to_json(evento_largo_clave(evento.key)))


    # Obtener todos los eventos existentes en el sistema, es el equivalente a filtrar
    # con un filtro vacio, sirve estando logueado o no
    def get(self):
        _, usuario = get_user_from_token(self.request.headers.get('bearer'), raise_for_unauthenticated=False)

        eventos = buscar_evento_categorias(usuario)

        # Devolver respuesta
        self.response.write(eventos_json(eventos, True))


def modificarDatosFlickr(evento, userId=None, albumId=None):
    """
    :param evento: ndb.Evento El evento que se va a almacenar en la base de datos
    :param userId: string id de usuario como cadena que manda el cliente
    :param albumId: string id de album como cadena proporcionada por el cliente
    :return: void
    """
    if (userId is not None) and (albumId is not None):
        if not albumId or albumId != evento.flickrAlbumId:
            evento.flickrAlbumId = albumId

        if not userId or userId != evento.flickrUserId:
            evento.flickrUserId = userId

            expresion = re.compile('\d+@N\d{2}')

            if userId and not(expresion.match(userId)):
                # Se obtiene empleando la API de flickr el user ID
                url_peticion = "http://www.flickr.com/photos/{}/".format(userId)
                print 'He hecho peticion!!!'
                # ID usuario
                idUsuario = flickr.urls.lookup_user(url_peticion)

                evento.flickrUserId = idUsuario

            if not evento.flickrUserId:
                # Lanzar excepcion de incidencia con flickr
                raise AgendamlgException.flickr_username_invalido(userId)




