from typing import List, Union
import warnings
from strenum import StrEnum
from pathlib import Path
from collections import defaultdict
import json
from json import JSONDecodeError

from bot.utils.singleton import Singleton


class User:
    def __init__(self, nickname):
        self.nickname = nickname
        self._authorized = False

    def __eq__(self, obj: object) -> bool:
        nick = getattr(obj, 'nickname', None)
        if nick is not None and isinstance(nick, str) and self.nickname == nick:
            return True
        
        return False
    
    @property
    def is_authorized(self):
        """Was granated access by admin"""
        return self._authorized
    
    @is_authorized.setter
    def is_authorized(self, true_false):
        self._authorized = true_false
    


# used to match ReportType constants by tg bot
_RECIPIENT_RIGHT_PREFIX = '#REC_'

class ReportType(StrEnum):
    # ContractStatus is not null and no ContractItems
    REC_CONTRACTS_NO_ITEMS = _RECIPIENT_RIGHT_PREFIX + 'ContractsNoItems'
    # 223 Однопоз однолот с типом лс без контракта
    REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223 = _RECIPIENT_RIGHT_PREFIX + 'OdnopozOdnolotLsNoContract223'


class UserAccessWarning(Warning):
    pass

class UnkownUserWarning(UserAccessWarning):
    pass

class KnownUserWarning(UserAccessWarning):
    pass

class UserRightsWarning(UserAccessWarning):
    pass

warnings.filterwarnings(action='ignore', category=UserRightsWarning)


class UserAccess(metaclass=Singleton):

    def __init__(self):
        self._dump_filename = '.user_access_dump.json'

        # all users who tried to access the bot
        self._users: List[User] = []

        # lists of users subscribed to certain mailings
        self._recip_contracts_no_items: List[User] = []
        self._recip_odnopoz_odnolot_ls_no_contract_223: List[User] = []

        self._alias_to_right = {
            ReportType.REC_CONTRACTS_NO_ITEMS: self._recip_contracts_no_items, 
            ReportType.REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223: self._recip_odnopoz_odnolot_ls_no_contract_223
        }

    def add_authorized(
        self, 
        users: Union[List[User], User]
    ) -> None:
        users = self._to_list(users)

        for new_user in users:
            for i, old_user in enumerate(self._users):
                if new_user == old_user:
                    self._users[i]._authorized = True
                    break
            else:   # no break occured
                new_user._authorized = True
                self._users.append(new_user)

    def add_unauthorized(
        self, 
        users: Union[List[User], User]
    ) -> None:
        users = self._to_list(users)

        for new_user in users:
            for i, old_user in enumerate(self._users):
                if new_user == old_user:
                    self._users[i]._authorized = False
                    for right_alias in self._alias_to_right.keys():
                        self.remove_acces(self._users[i], right_alias)
                    break
            else:   # no break occured
                new_user._authorized = False
                self._users.append(new_user)

    def get_authorized_users(self) -> List[User]:
        return [usr for usr in self._users if usr.is_authorized]

    def get_unauthorized_users(self) -> List[User]:
        return [usr for usr in self._users if not usr.is_authorized]
    

    def grant_acces(
        self,
        users: Union[List[User], User],
        alias: str
    ) -> None:
        users = self._to_list(users)

        if self._check_valid_right_alias(alias):
            pass

        for user in users:
            if user in self._users:
                access_right_list = self._alias_to_right[alias]
                if user not in access_right_list:
                    access_right_list.append(user)
                else:
                    warnings.warn(f"Right already granted for user {user.nickname}", UserRightsWarning)
            else:
                raise warnings.warn(f"Unkown user {user.nickname}", UnkownUserWarning)
          
    def remove_acces(
        self,
        users: Union[List[User], User],
        alias: str
    ) -> None:
        users = self._to_list(users)

        if self._check_valid_right_alias(alias):
            pass

        for user in users:
            if user in self._users:
                access_right_list = self._alias_to_right[alias]
                if user in access_right_list:
                    access_right_list.remove(user)
                else:
                    warnings.warn(f"Right already disabled for user {user.nickname}", UserRightsWarning)
            else:
                raise warnings.warn(f"Unkown user {user.nickname}", UnkownUserWarning)
            

    def is_granted(self, user: User, alias: str) -> bool:
        if self._check_valid_right_alias(alias):
            pass

        return user in self._alias_to_right[alias]
    

    def dump_all(self, input_path=None):
        path = self._construct_path(
            input_path,
            self._dump_filename)

        # write user access data
        with open(path, 'w+') as f:
            user_access_dict = defaultdict(dict)
            for u in self._users:
                if u.is_authorized:

                    user_access_dict[u.nickname]['auth'] = True
                    user_access_dict[u.nickname]['rights'] = []
                    for rep_list in self._alias_to_right.items():
                        if u in rep_list[1]:    # recipient list
                            user_access_dict[u.nickname]['rights'].append(rep_list[0])    # right identifier
                else:
                    user_access_dict[u.nickname]['auth'] = False

            json.dump(user_access_dict, f)


    def recover_from_dump(self, input_path=None):
        path = self._construct_path(
            input_path,
            self._dump_filename)
        if not path.exists():   # on startup path doesnt exist
            return

        with open(path) as f:
            dump_content = f.read()

        try:
            user_access_dict = json.loads(dump_content)
        except JSONDecodeError:
            return
        
        for u_nick, u_data in user_access_dict.items():
            user = User(u_nick)
            if u_data['auth']:
                self.add_authorized(user)
                for right_alias in u_data['rights']:
                    self.grant_acces(user, right_alias)
            else:
                self.add_unauthorized(user)
            

    def _check_valid_right_alias(self, alias: str) -> bool:
        if alias not in self._alias_to_right.keys():
            raise Exception(f"Unkown acces right: {alias}")
        
    @staticmethod
    def _to_list(users: Union[List[User], User]):
        if isinstance(users, User):
            return [users]
        return users
    
    @staticmethod
    def _construct_path(input_path, candidate_path):
        if input_path is None:
            input_path = candidate_path

        path = Path(input_path)
        if not path.exists():
            path = Path(__file__).parent / input_path
        if path.is_dir():
            path = path / candidate_path

        return path
