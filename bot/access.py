from typing import List, Union
import warnings

class User:
    def __init__(self, nickname):
        self.nickname = nickname
        self._authorized = False

    def __eq__(self, obj: object) -> bool:
        nick = getattr(obj, 'nickname', None)
        if nick is not None and isinstance(nick, str) and self.nickname == nick:
            return True
        
        return False
    
    def is_authorized(self):
        """Was granated access by admin"""
        return self._authorized
    


class UserAccessWarning(Warning):
    pass

class UnkownUserWarning(UserAccessWarning):
    pass

class KnownUserWarning(UserAccessWarning):
    pass

class UserRightsWarning(UserAccessWarning):
    pass


class UserAccess:

    def __init__(self):
        # all users who tried to access the bot
        self._users: List[User] = []
        # users with access to mailing for contracts with no items and invalid status
        self._contracts_no_items_recip: List[User] = []

        self._alias_to_right = {
            'ContractsNoItems': self._contracts_no_items_recip
        }

    def add_authorized(
        self, 
        users: Union[List[User], User]
    ) -> None:
        for user in users:
            user._authorized = True
            if user not in self._users:
                self._users.append(user)

    def add_unauthorized(
        self, 
        users: Union[List[User], User]
    ) -> None:
        for user in users:
            user._authorized = False
            if user not in self._users:
                self._users.append(user)

    def get_authorized_users(self) -> List[User]:
        return [usr for usr in self._users if usr.is_authorized()]

    def get_unauthorized_users(self) -> List[User]:
        return [usr for usr in self._users if not usr.is_authorized()]
    

    def grant_acces(
        self,
        users: Union[List[User], User],
        alias: str
    ) -> None:
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

    def _check_valid_right_alias(self, alias: str) -> bool:
        if alias not in self._alias_to_right.keys():
            raise Exception("Unkown acces right")
