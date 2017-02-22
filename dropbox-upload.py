#!/usr/bin/env python2.7
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import sys, dropbox, os

app_key = 'xxxxxxxxxxxxxxx'
app_secret = 'xxxxxxxxxxxxxxx'
access_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

def authorize():
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = flow.start()
    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'
    code = raw_input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    return access_token

def upload(file):
    client = dropbox.client.DropboxClient(access_token)
    #print 'Linked account: ', client.account_info()
    with open(file, 'rb') as f:
        response = client.put_file(os.path.basename(file), f, overwrite=True)
        #print 'Uploaded: ', response

if __name__ == '__main__':
    if access_token is None:
        access_token = authorize()
        sys.exit('Embed this access token into this script, then re-run: %s' % access_token)

    if len(sys.argv) != 2:
        sys.exit("USAGE: %s <file to upload>" % sys.argv[0])

    upload(sys.argv[1])

