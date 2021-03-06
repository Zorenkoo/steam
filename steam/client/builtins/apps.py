import vdf
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto


class Apps(object):
    def __init__(self, *args, **kwargs):
        super(Apps, self).__init__(*args, **kwargs)

    def get_player_count(self, app_id, timeout=5):
        """Get numbers of players for app id

        :param app_id: app id
        :type app_id: :class:`int`
        :return: number of players
        :rtype: :class:`int`, :class:`.EResult`
        """
        resp = self.send_job_and_wait(MsgProto(EMsg.ClientGetNumberOfCurrentPlayersDP),
                                      {'appid': app_id},
                                      timeout=timeout
                                     )
        if resp is None:
            return EResult.Timeout
        elif resp.eresult == EResult.OK:
            return resp.player_count
        else:
            return EResult(resp.eresult)

    def get_product_info(self, apps=[], packages=[], timeout=15):
        """Get product info for apps and packages

        :param apps: items in the list should be either just ``app_id``, or ``(app_id, access_token)``
        :type apps: :class:`list`
        :param packages: items in the list should be either just ``package_id``, or ``(package_id, access_token)``
        :type packages: :class:`list`
        :return: dict with ``apps`` and ``packages`` containing their info, see example below
        :rtype: :class:`dict`, :class:`None`

        .. code:: python

            {'apps':     {570: {...}, ...},
             'packages': {123: {...}, ...}
            }
        """
        if not apps and not packages: return

        message = MsgProto(EMsg.ClientPICSProductInfoRequest)

        for app in apps:
                app_info = message.body.apps.add()
                app_info.only_public = False
                if isinstance(app, tuple):
                        app_info.appid, app_info.access_token = app
                else:
                        app_info.appid = app

        for package in packages:
                package_info = message.body.packages.add()
                if isinstance(package, tuple):
                        package_info.appid, package_info.access_token = package
                else:
                        package_info.packageid = package

        message.body.meta_data_only = False

        job_id = self.send_job(message)

        data = dict(apps={}, packages={})

        while True:
            chunk = self.wait_event(job_id, timeout=timeout)

            if chunk is None: return
            chunk = chunk[0].body

            for app in chunk.apps:
                data['apps'][app.appid] = vdf.loads(app.buffer[:-1].decode('utf-8', 'replace'))['appinfo']
            for pkg in chunk.packages:
                data['packages'][pkg.packageid] = vdf.binary_loads(pkg.buffer[4:])[str(pkg.packageid)]

            if not chunk.response_pending:
                break

        return data

    def get_changes_since(self, change_number, app_changes=True, package_changes=False):
        """Get changes since a change number

        :param change_number: change number to use as stating point
        :type change_number: :class:`int`
        :param app_changes: whether to inclued app changes
        :type app_changes: :class:`bool`
        :param package_changes: whether to inclued package changes
        :type package_changes: :class:`bool`
        :return: `CMsgClientPICSChangesSinceResponse <https://github.com/ValvePython/steam/blob/39627fe883feeed2206016bacd92cf0e4580ead6/protobufs/steammessages_clientserver.proto#L1171-L1191>`_
        :rtype: proto message instance, or :class:`None` on timeout
        """
        return self.send_job_and_wait(MsgProto(EMsg.ClientPICSChangesSinceRequest),
                                      {
                                       'since_change_number': change_number,
                                       'send_app_info_changes': app_changes,
                                       'send_package_info_changes': package_changes,
                                      },
                                      timeout=15
                                     )

    def get_app_ticket(self, app_id):
        """Get app ownership ticket

        :param app_id: app id
        :type app_id: :class:`int`
        :return: `CMsgClientGetAppOwnershipTicketResponse <https://github.com/ValvePython/steam/blob/39627fe883feeed2206016bacd92cf0e4580ead6/protobufs/steammessages_clientserver.proto#L158-L162>`_
        :rtype: proto message
        """
        return self.send_job_and_wait(MsgProto(EMsg.ClientGetAppOwnershipTicket),
                                      {'app_id': app_id},
                                      timeout=15
                                     )

    def get_depot_key(self, depot_id, app_id=0):
        """Get depot decryption key

        :param depot_id: depot id
        :type depot_id: :class:`int`
        :param app_id: app id
        :type app_id: :class:`int`
        :return: `CMsgClientGetDepotDecryptionKeyResponse <https://github.com/ValvePython/steam/blob/39627fe883feeed2206016bacd92cf0e4580ead6/protobufs/steammessages_clientserver_2.proto#L533-L537>`_
        :rtype: proto message
        """
        return self.send_job_and_wait(MsgProto(EMsg.ClientGetDepotDecryptionKey),
                                      {
                                       'depot_id': depot_id,
                                       'app_id': app_id,
                                      },
                                      timeout=15
                                     )

    def get_cdn_auth_token(self, app_id, hostname):
        """Get CDN authentication token

        :param app_id: app id
        :type app_id: :class:`int`
        :param hostname: cdn hostname
        :type hostname: :class:`str`
        :return: `CMsgClientGetCDNAuthTokenResponse <https://github.com/ValvePython/steam/blob/39627fe883feeed2206016bacd92cf0e4580ead6/protobufs/steammessages_clientserver_2.proto#L585-L589>`_
        :rtype: proto message
        """
        return self.send_job_and_wait(MsgProto(EMsg.ClientGetCDNAuthToken),
                                      {
                                       'app_id': app_id,
                                       'host_name': hostname,
                                      },
                                      timeout=15
                                     )

    def get_product_access_tokens(self, app_ids=[], package_ids=[]):
        """Get access tokens

        :param app_ids: list of app ids
        :type app_ids: :class:`list`
        :param package_ids: list of package ids
        :type package_ids: :class:`list`
        :return: dict with ``apps`` and ``packages`` containing their access tokens, see example below
        :rtype: :class:`dict`, :class:`None`

        .. code:: python

            {'apps':     {123: 'token', ...},
             'packages': {456: 'token', ...}
            }
        """
        if not app_ids and not package_ids: return

        resp = self.send_job_and_wait(MsgProto(EMsg.ClientPICSAccessTokenRequest),
                                      {
                                       'appids': map(int, app_ids),
                                       'packageids': map(int, package_ids),
                                      },
                                      timeout=15
                                     )

        if resp:
            return {'apps': dict(map(lambda app: (app.appid, app.access_token), resp.app_access_tokens)),
                    'packages': dict(map(lambda pkg: (pkg.appid, pkg.access_token), resp.package_access_tokens)),
                   }

    def register_product_key(self, key):
        """Register/Redeem a CD-Key

        :param key: CD-Key
        :type  key: :class:`str`
        :return: format ``(eresult, result_details, receipt_info)``
        :rtype: :class:`tuple`

        Example ``receipt_info``:

        .. code:: python

            {'BasePrice': 0,
              'CurrencyCode': 0,
              'ErrorHeadline': '',
              'ErrorLinkText': '',
              'ErrorLinkURL': '',
              'ErrorString': '',
              'LineItemCount': 1,
              'PaymentMethod': 1,
              'PurchaseStatus': 1,
              'ResultDetail': 0,
              'Shipping': 0,
              'Tax': 0,
              'TotalDiscount': 0,
              'TransactionID': UINT_64(111111111111111111),
              'TransactionTime': 1473000000,
              'lineitems': {'0': {'ItemDescription': 'Half-Life 3',
                'TransactionID': UINT_64(11111111111111111),
                'packageid': 1234}},
              'packageid': -1}
        """
        resp = self.send_job_and_wait(MsgProto(EMsg.ClientRegisterKey),
                                      {'key': key},
                                      timeout=30,
                                      )

        if resp:
            details = vdf.binary_loads(resp.purchase_receipt_info).get('MessageObject', None)
            return EResult(resp.eresult), resp.purchase_result_details, details
        else:
            return EResult.Timeout, None, None
