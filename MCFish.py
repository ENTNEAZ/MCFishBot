#!/usr/bin/env python
'''修改于原Start.py'''
from __future__ import print_function

import getpass
import sys
import re
import time
import json
from optparse import OptionParser

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound
from minecraft.compat import input
from minecraft.networking.types.utility import Vector
import minecraft.networking.packets.serverbound.play

NewThrow = True
InPosition = Vector(0,0,0)
def get_options():
    parser = OptionParser()

    parser.add_option("-u", "--username", dest="username", default=None,
                      help="username to log in with")

    parser.add_option("-p", "--password", dest="password", default=None,
                      help="password to log in with")

    parser.add_option("-s", "--server", dest="server", default=None,
                      help="server host or host:port "
                           "(enclose IPv6 addresses in square brackets)")

    parser.add_option("-o", "--offline", dest="offline", action="store_true",
                      help="connect to a server in offline mode "
                           "(no password required)")

    parser.add_option("-d", "--dump-packets", dest="dump_packets",
                      action="store_true",
                      help="print sent and received packets to standard error")

    (options, args) = parser.parse_args()
    
    if not options.username:
        options.username = input("Enter your username: ")

    if not options.password and not options.offline:
        options.password = getpass.getpass("Enter your password (leave "
                                           "blank for offline mode): ")
        options.offline = options.offline or (options.password == "")

    if not options.server:
        options.server = input("Enter server host or host:port "
                               "(enclose IPv6 addresses in square brackets): ")
    # Try to split out port and address
    match = re.match(r"((?P<host>[^\[\]:]+)|\[(?P<addr>[^\[\]]+)\])"
                     r"(:(?P<port>\d+))?$", options.server)
    if match is None:
        raise ValueError("Invalid server address: '%s'." % options.server)
    options.address = match.group("host") or match.group("addr")
    options.port = int(match.group("port") or 25565)
    return options

def useitem():
    global connection
    global packet
    connection.write_packet(packet)



options = get_options()
if options.offline:
    print("Connecting in offline mode...")
    connection = Connection(
        options.address, options.port, username=options.username)
else:
    auth_token = authentication.AuthenticationToken()
    try:
        auth_token.authenticate(options.username, options.password)
    except YggdrasilError as e:
        print(e)
        sys.exit()
    print("Logged in as %s..." % auth_token.username)
    connection = Connection(
        options.address, options.port, auth_token=auth_token)

packet = minecraft.networking.packets.serverbound.play.UseItemPacket()
packet.hand = 0

if options.dump_packets:
    def print_incoming(packet):
        if type(packet) is Packet:
            # This is a direct instance of the base Packet type, meaning
            # that it is a packet of unknown type, so we do not print it.
            return
        print('--> %s' % packet, file=sys.stderr)

    def print_outgoing(packet):
        print('<-- %s' % packet, file=sys.stderr)

    connection.register_packet_listener(
        print_incoming, Packet, early=True)
    connection.register_packet_listener(
        print_outgoing, Packet, outgoing=True)


def handle_join_game(join_game_packet):
    print('Connected.')

def print_chat(chat_packet):
    # TODO 聊天信息正常化


    #print(chat_packet.json_data)
    decode = json.loads(chat_packet.json_data)
        
        
    try:
        print('<' + decode['with'][0]['text'] + '> ' + decode['with'][1],end = '')
    except:
        print(decode)
        
    
def sound(sound):
    global NewThrow
    global InPosition
    if sound.sound_id == 73:
        print('有上钩的声音')
        if (InPosition - sound.effect_position).norm() < 3 :
            print('是我的，收竿')
            useitem()
            print('扔竿')

            useitem()  
            NewThrow = True
        else:
            print('远处的钓鱼声，不是我的')
        
    if sound.sound_id == 258 and NewThrow:
        NewThrow = False
        InPosition = sound.effect_position


connection.register_packet_listener(
    handle_join_game, clientbound.play.JoinGamePacket)
    
connection.register_packet_listener(
    print_chat, clientbound.play.ChatMessagePacket)


connection.register_packet_listener(
    sound, clientbound.play.SoundEffectPacket)

connection.connect()
time.sleep(3)
useitem()
    
    
while True:
    try:
        text = input()
        if text == "/respawn":
            print("respawning...")
            packet = serverbound.play.ClientStatusPacket()
            packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
            connection.write_packet(packet)
        else:
            packet = serverbound.play.ChatPacket()
            packet.message = text
            connection.write_packet(packet)
    except KeyboardInterrupt:
        print("Bye!")
        sys.exit()