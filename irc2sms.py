#!/usr/bin/env python2

import argparse, sys, time, yaml, zmq
from googlevoice import Voice

p = argparse.ArgumentParser(description="irc2sms");
p.add_argument('-i', '--ignore', metavar='NICK', default='', nargs='+', help='nicks to ignore');
p.add_argument('-s', '--source', default='tcp://*:2428', help='ZeroMQ source');
p.add_argument('-d', '--destination', required=True, help='phone number to send sms to');
args = p.parse_args();

print "Connecting to Google Voice... ",
voice = Voice();
voice.login();
print "done!"

context = zmq.Context();
 
subscriber = context.socket(zmq.SUB);
subscriber.connect(args.source);
subscriber.setsockopt(zmq.SUBSCRIBE, "");

while True:
    try:
        rx = subscriber.recv();

        # lolololol this is dumb -- it seems to be a difference between the
        # ruby implementation of ZeroMQ and the Python implementation
        rx = rx.replace('!binary', '!!binary');

        data = yaml.load(rx);

        if data[':away']:

            ignicks = [ _ for _ in args.ignore if 'nick_'+_ in data[':tags'] ]
            if len(ignicks) != 0:
                print "Message from ignored nick %s" % ignicks[0];
            
            elif data[':message'][:15] == "Day changed to " and len(data[':tags']) == 0:
                print "Day changed message from %s %s" % (data['server'], data['channel']);
                
            elif data[':message'][-18:] == " is back on server" and len(data[':tags']) == 0:
                print "Back on server message for %s %s" % (data['server'], data['channel']);
                
            else:
                # status was away and message wasn't from an ignored nick, so it's
                # safe to send
                if data[':type'] == 'private':
                    msg = "%s: %s" % (data[':channel'], data[':message']);
                else:
                    sender = "";
                    for _ in data[':tags']:
                        if _[0:5] == 'nick_':
                            sender = _[5:];
                    msg = "[%s %s] %s: %s" % (data['server'], data['channel'],
                            sender, data['message']);

                voice.send_sms(args.destination, msg);
                print "Message from %s" % msg.split(':')[0];

    except KeyboardInterrupt:
        print "Goodbye!"
        voice.logout();
        sys.exit(0);

    except:
        print "Error!"
