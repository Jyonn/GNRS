from torch import nn

from loader.global_setting import Setting
from model.common.attention import AdditiveAttention
from model.operator.attention_operator import AttentionOperatorConfig
from model.operator.base_operator import BaseOperator
from model.inputer.concat_inputer import ConcatInputer

from transformers.models.bert.modeling_bert import BertModel, BertConfig


class TransformerOperatorConfig(AttentionOperatorConfig):
    def __init__(
            self,
            num_hidden_layers: int = 3,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self.num_hidden_layers = num_hidden_layers


class TransformerOperator(BaseOperator):
    config_class = TransformerOperatorConfig
    inputer_class = ConcatInputer
    config: TransformerOperatorConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.target_user:
            embed_dim = self.config.hidden_size
        else:
            embed_dim = self.config.embed_hidden_size

        self.transformer = BertModel(BertConfig(
            hidden_size=embed_dim,
            num_attention_heads=self.config.num_attention_heads,
            attention_probs_dropout_prob=self.config.attention_dropout,
            num_hidden_layers=self.config.num_hidden_layers,
            intermediate_size=self.config.hidden_size * 4,
            vocab_size=1,
            type_vocab_size=1,
        ))

        self.linear = nn.Linear(embed_dim, self.config.hidden_size)

        self.additive_attention = AdditiveAttention(
            embed_dim=self.config.hidden_size,
            hidden_size=self.config.hidden_size,
        )

    def forward(self, embeddings, mask=None, **kwargs):
        mask = mask.to(Setting.device)

        transformer_output = self.transformer(
            inputs_embeds=embeddings,
            attention_mask=mask,
            return_dict=True,

        )
        outputs = transformer_output.last_hidden_state  # [B, L, D]

        outputs = self.linear(outputs)  # [B, L, D]
        outputs = self.additive_attention(outputs, mask)  # [B, D]

        return outputs
