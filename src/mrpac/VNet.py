import torch
import torch.nn as nn


def get_norm(norm_type, num_channels, num_groups=8):
    if norm_type == "group":
        return nn.GroupNorm(num_groups=num_groups, num_channels=num_channels)
    elif norm_type == "instance":
        return nn.InstanceNorm3d(num_channels)
    else:
        raise ValueError(f"Unsupported norm_type: {norm_type}")


class ResidualBlock(nn.Module):
    def __init__(
        self, in_channels, out_channels, dropout_p=0.2, norm_type="instance", num_groups=8
    ):
        super().__init__()
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1)
        self.norm1 = get_norm(norm_type, out_channels, num_groups)
        self.act1 = nn.PReLU()
        self.dropout = nn.Dropout3d(p=dropout_p)

        self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1)
        self.norm2 = get_norm(norm_type, out_channels, num_groups)
        self.act2 = nn.PReLU()

        self.skip_conv = None
        if in_channels != out_channels:
            self.skip_conv = nn.Conv3d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        identity = x if self.skip_conv is None else self.skip_conv(x)

        out = self.dropout(self.act1(self.norm1(self.conv1(x))))
        out = self.norm2(self.conv2(out))
        out = self.act2(out + identity)
        return out


class EncoderBlock(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels,
        down=True,
        dropout_p=0.2,
        norm_type="instance",
        num_groups=8,
    ):
        super().__init__()
        self.down = down
        if down:
            self.down_conv = nn.Conv3d(in_channels, out_channels, kernel_size=2, stride=2)
        else:
            self.down_conv = nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1)

        self.norm = get_norm(norm_type, out_channels, num_groups)
        self.act = nn.PReLU()
        self.dropout = nn.Dropout3d(p=dropout_p)
        self.res_block = ResidualBlock(
            out_channels, out_channels, dropout_p, norm_type, num_groups
        )

    def forward(self, x):
        x = self.dropout(self.act(self.norm(self.down_conv(x))))
        skip = x
        x = self.res_block(x)
        return x, skip


class DecoderBlock(nn.Module):
    def __init__(
        self, in_channels, out_channels, dropout_p=0.2, norm_type="instance", num_groups=8
    ):
        super().__init__()
        self.up_conv = nn.ConvTranspose3d(in_channels, out_channels, kernel_size=2, stride=2)
        self.norm = get_norm(norm_type, out_channels, num_groups)
        self.act = nn.PReLU()
        self.dropout = nn.Dropout3d(p=dropout_p)
        self.res_block = ResidualBlock(
            out_channels, out_channels, dropout_p, norm_type, num_groups
        )

    def forward(self, x, skip):
        x = self.dropout(self.act(self.norm(self.up_conv(x))))
        x = x + skip
        return self.res_block(x)


class Bottleneck(nn.Module):
    def __init__(
        self, in_channels, out_channels, dropout_p=0.2, norm_type="instance", num_groups=8
    ):
        super().__init__()
        self.down_conv = nn.Conv3d(in_channels, out_channels, kernel_size=2, stride=2)
        self.res_block = ResidualBlock(
            out_channels, out_channels, dropout_p, norm_type, num_groups
        )

    def forward(self, x):
        x = self.down_conv(x)
        return self.res_block(x)


class VNet(nn.Module):
    def __init__(
        self,
        in_channels=1,
        out_channels=2,
        base_filters=16,
        num_layers=4,
        dropout_p=0.2,
        norm_type="instance",
        num_groups=8,
    ):
        super().__init__()

        self.enc_blocks = nn.ModuleList()
        self.dec_blocks = nn.ModuleList()

        # Encoder
        self.enc_blocks.append(
            EncoderBlock(
                in_channels,
                base_filters,
                down=False,
                dropout_p=dropout_p,
                norm_type=norm_type,
                num_groups=num_groups,
            )
        )
        for i in range(1, num_layers):
            in_ch = base_filters * 2 ** (i - 1)
            out_ch = base_filters * 2**i
            self.enc_blocks.append(
                EncoderBlock(
                    in_ch,
                    out_ch,
                    down=True,
                    dropout_p=dropout_p,
                    norm_type=norm_type,
                    num_groups=num_groups,
                )
            )

        # Bottleneck
        self.bottleneck = Bottleneck(
            base_filters * 2 ** (num_layers - 1),
            base_filters * 2**num_layers,
            dropout_p=dropout_p,
            norm_type=norm_type,
            num_groups=num_groups,
        )

        # Decoder
        for i in reversed(range(num_layers)):
            in_ch = base_filters * 2 ** (i + 1)
            out_ch = base_filters * 2**i
            self.dec_blocks.append(
                DecoderBlock(
                    in_ch, out_ch, dropout_p=dropout_p, norm_type=norm_type, num_groups=num_groups
                )
            )

        # Output
        self.out_conv = nn.Conv3d(base_filters, out_channels, kernel_size=1)

    def forward(self, x):
        skips = []
        for block in self.enc_blocks:
            x, skip = block(x)
            skips.append(skip)

        x = self.bottleneck(x)

        for block in self.dec_blocks:
            x = block(x, skips.pop())

        return self.out_conv(x)


if __name__ == "__main__":
    model = VNet(in_channels=1, out_channels=3, base_filters=32, num_layers=4)
    # Total parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params}")

    # Trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {trainable_params}")
    x = torch.randn(2, 1, 64, 128, 128)
    y = model(x)
    print("Output shape:", y.shape)
