import torch
import torch.nn as nn
from torch.utils.data import Dataset


class TunedLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze(1)


class SlidingWindowDataset(Dataset):
    def __init__(self, X, y, seq_len=10):
        self.X_seq = []
        self.y = []

        for i in range(len(X) - seq_len):
            self.X_seq.append(X.iloc[i:i+seq_len].values)
            self.y.append(y.iloc[i+seq_len])

        self.X_seq = torch.tensor(self.X_seq, dtype=torch.float32)
        self.y = torch.tensor(self.y, dtype=torch.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X_seq[idx], self.y[idx]