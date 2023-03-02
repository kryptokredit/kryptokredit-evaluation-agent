import structlog
import pydantic
from typing import Any, Dict, List, ClassVar
from huma_signals import models
from huma_signals.adapters import models as adapter_models
from huma_signals.settings import settings
from graphqlclient import GraphQLClient

logger = structlog.get_logger()

class KryptoKreditSignals(models.HumaBaseModel):
    total_invoices: int
    total_paid_invoices: int
    total_received_invoices: int
    total_derogetory_marks: int
    avg_value_of_invoices: float
    avg_value_of_payments: float
    avg_value_of_recients: float

class KryptoKreditAdapter(adapter_models.SignalAdapterBase):
    name: ClassVar[str] = "krypto_kredit_adapter"
    required_inputs: ClassVar[List[str]] = ["borrower_address"]
    signals: ClassVar[List[str]] = ["total_debt", "collateral_ratio", "liquidation_price"]

    graphql_endpoint: str = pydantic.Field(default=settings.krypto_kredit_graphql_endpoint)
    
    @pydantic.validator("graphql_endpoint")
    def validate_graphql_endpoint(cls, value: str) -> str:
        if not value:
            raise ValueError("graphql_endpoint is required")
        return value
    
    @classmethod
    async def _node_get_transactions(
        cls, wallet_address: str, graphql_endpoint: str
    ) -> List[Any]:
        try:
            client = GraphQLClient(cls.graphql_endpoint)
            query = '''
                {
                    invoicePaids(where: { payer: "%s" }, orderBy: id) {
                        id
                        dueDate
                        date
                    }
                }
            '''.format(wallet_address)
            result = client.execute(query)
            data = json.loads(result)["data"]["invoicePaids"]
            return data
        except Exception as e:
            logger.error("Error fetching data from Krypto Kredit GraphQL API", exc_info=True, borrower_address=borrower_address)
            return {"error": str(e)}

        return []
        
    async def fetch(  # pylint: disable=arguments-differ
        self, borrower_wallet_address: str, *args: Any, **kwargs: Any
    ) -> KryptoKreditSignals:
        raw_txns = await self._node_get_transactions(
            borrower_wallet_address,
            etherscan_base_url=self.etherscan_base_url,
        )
        txn_df = pd.DataFrame.from_records(raw_txns)
        if len(txn_df) == 0:
            return KryptoKreditSignals(
                total_invoices=0,
                total_paid_invoices=0,
                total_received_invoices=0,
                total_derogetory_marks=0,
                avg_value_of_invoices=0,
                avg_value_of_payments=0,
                avg_value_of_recients=0,
            )

        txn_df["datetime"] = pd.to_datetime(txn_df["timeStamp"], unit="s")
        txn_df["total_invoices"] = txn_df["value"].astype(float)
        txn_df["total_paid_invoices"] = txn_df["from"].str.lower()
        txn_df["total_received_invoices"] = txn_df["to"].str.lower()
        txn_df["total_derogetory_marks"] = txn_df["to"].str.lower()
        txn_df["avg_value_of_invoices"] = txn_df["from"] == borrower_wallet_address.lower()
        txn_df["avg_value_of_payments"] = txn_df["to"] == borrower_wallet_address.lower()
        txn_df["avg_value_of_recients"] = txn_df[]

        return KryptoKreditSignals(
            total_transactions=len(txn_df),
            total_sent=sum(txn_df["is_sent"]),
            total_received=sum(txn_df["is_received"]),
            wallet_tenure_in_days=(
                datetime.datetime.now() - txn_df["timeStamp"].min()
            ).days,
            total_income_90days=sum(txn_df["income"] * txn_df["in_90days"]),
            total_transactions_90days=sum(txn_df["in_90days"]),
        )