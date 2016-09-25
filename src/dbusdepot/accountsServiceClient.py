#! /usr/bin/python3

from gi.repository import GObject, AccountsService

from util import utils

class AccountsServiceClient(GObject.Object):
    __gsignals__ = {
        'account-loaded': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(AccountsServiceClient, self).__init__()

        self.is_loaded = False
        self.real_name = None
        self.face_path = None

        self.service = AccountsService.UserManager.get_default().get_user(utils.get_user_name())
        trackers.con_tracker_get().connect(self.service,
                                           "notify::is-loaded",
                                           self.on_accounts_service_loaded)

    def on_accounts_service_loaded(self, service, param):
        self.real_name = service.get_real_name()

        for path in [os.path.join(service.get_home_dir(), ".face"),
                     service.get_icon_file(),
                     "/usr/share/cinnamon/faces/user-generic.png"]:
            if os.path.exists(path):
                self.face_path = path
                break

        self.is_loaded = True
        self.emit("account-loaded")
