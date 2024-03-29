from model.operator.ada_operator import AdaOperator
from model.operator.cnn_operator import CNNOperator
from model.recommenders.dcn_model import DCNModel, DCNModelConfig


class NAMLDCNModel(DCNModel):
    news_encoder_class = CNNOperator
    user_encoder_class = AdaOperator

    def __init__(self, config: DCNModelConfig, **kwargs):
        super().__init__(input_dim=config.hidden_size, config=config, **kwargs)
