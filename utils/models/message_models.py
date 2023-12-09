import uuid
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class DailyReading(BaseModel):
    heartRate: int
    steps: int
    sleepDuration: int

class Stats(BaseModel):
    height: int
    weight: int

class UserData(BaseModel):
    details: List[DailyReading]
    moreDetails: List[Stats]

class MoreUserDetailsEvent(BaseModel):
    userId: str
    height: int
    weight: int

class UserDetailsEvent(BaseModel):
    userId: str
    heartRate: int
    steps: int
    sleepDuration: int

class UpdateStatePayload(BaseModel):
    height: int
    weight: int

class UpdateDailyReadingPayload(BaseModel):
    details: DailyReading

class LoomGroomContract(BaseModel):
    userId: str
    moreDetails: UpdateStatePayload
    details: UpdateDailyReadingPayload

class SnapshotBase(BaseModel):
    contract: str
    chainHeightRange: Dict[str, int]
    timestamp: int

class MoreUserDetailsSnapshot(SnapshotBase):
    userId: str
    height: int
    weight: int


class UserDetailsSnapshot(SnapshotBase):
    activities: List[UserDetailsEvent]

class LoomGroomSnapshot(BaseModel):
    userId: str
    moreDetails: MoreUserDetailsSnapshot
    details: UserDetailsSnapshot