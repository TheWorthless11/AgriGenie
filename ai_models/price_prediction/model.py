"""
PyTorch LSTM model for crop price prediction.
Multivariate LSTM with dropout, designed to consume VMD-decomposed + feature inputs.
"""

import torch
import torch.nn as nn


class PriceLSTM(nn.Module):
    """
    Multivariate LSTM for next-month price prediction.

    Parameters
    ----------
    input_size  : int   — number of features per time step
    hidden_size : int   — neurons per LSTM layer
    num_layers  : int   — stacked LSTM layers
    dropout     : float — dropout between LSTM layers (applied when num_layers > 1)
    """

    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x : (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Take the output of the last time step
        last_hidden = lstm_out[:, -1, :]
        return self.fc(last_hidden).squeeze(-1)
