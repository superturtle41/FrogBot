class SheetError(Exception):
    pass


class NoGuild(SheetError):
    pass


class NoOwner(SheetError):
    pass


class NoApprover(SheetError):
    pass


class NoChannel(SheetError):
    pass


class NoMessage(SheetError):
    pass
