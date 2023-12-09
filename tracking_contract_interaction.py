import json
from typing import List
from typing import Tuple
from typing import Union

import time
from redis import asyncio as aioredis

from .utils.event_log_decoder import EventLogDecoder
from .utils.models.message_models import UserDetailsSnapshot, UserDetailsEvent
from snapshotter.utils.callback_helpers import GenericProcessorSnapshot
from snapshotter.utils.default_logger import logger
from snapshotter.utils.models.message_models import EthTransactionReceipt
from snapshotter.utils.models.message_models import PowerloomSnapshotProcessMessage
from snapshotter.utils.redis.redis_keys import epoch_txs_htable
from snapshotter.utils.rpc import RpcHelper


class TrackingContractInteractionProcessor(GenericProcessorSnapshot):
    transformation_lambdas = None

    def __init__(self) -> None:
        self.transformation_lambdas = []
        self._logger = logger.bind(module='TrackingContractInteractionProcessor')

    async def compute(
        self,
        epoch: PowerloomSnapshotProcessMessage,
        redis_conn: aioredis.Redis,
        rpc_helper: RpcHelper,

    ) -> Union[None, List[Tuple[str, UserDetailsSnapshot]]]:
        min_chain_height = epoch.begin
        max_chain_height = epoch.end

        if max_chain_height != min_chain_height:
            self._logger.error('Currently only supports single block height')
            raise Exception('Currently only supports single block height')

        # get txs for this epoch
        txs_hset = await redis_conn.hgetall(epoch_txs_htable(epoch.epochId))
        all_txs = {k.decode(): EthTransactionReceipt.parse_raw(v) for k, v in txs_hset.items()}

        contract_address = epoch.data_source
        contract_txs = list(
            map(
                lambda x: x.dict(), filter(
                    lambda tx: tx.to == contract_address,
                    all_txs.values(),
                ),
            ),
        )

        with open('snapshotter/modules/computes/Abi.json') as f:
            abi = json.load(f)

        node = rpc_helper.get_current_node()
        w3 = node['web3_client']
        contract = w3.eth.contract(address=contract_address, abi=abi)

        eld = EventLogDecoder(contract)

        snapshots = []
        # min amount in wei
        # min_amount = 2000000000000000
        min_amount = 0
        processed_logs = []

        for tx_receipt in contract_txs:
            for log in tx_receipt['logs']:
                # Send (address receiver, uint256 amount, bytes32 srcChainTxHash) event log topic
                if log['topics'][0] == '0x9e2e662eaa46b0fc0ad0689f581ea50987c28baf7c78cda16b01e8979af5423c':
                    try:
                        log_decoded = eld.decode_log(log)
                        log_obj = UserDetailsEvent.parse_obj({
                            'userId': log_decoded['userId'],
                            'heartRate': log_decoded['heartRate'],
                            'sleepDuration': log_decoded['sleepDuration'],
                            'steps': log_decoded['steps']
                        })
                        processed_logs.append(log_obj)
                    except:
                        pass
        
        snapshot = UserDetailsSnapshot(
            activities=processed_logs,
            contract=contract_address,
            chainHeightRange = {"begin": min_chain_height, "end": max_chain_height},
            timestamp=int(time.time())
        )       
        return snapshot