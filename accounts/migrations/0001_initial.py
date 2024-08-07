# Generated by Django 4.2.7 on 2024-02-05 22:44

import accounts.managers.users
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('user_type', models.CharField(choices=[('BUYER', 'buyer'), ('INVESTOR', 'investor'), ('AGENT', 'agent'), ('COMPANY', 'company'), ('EXTERNAL', 'external')], db_index=True, default='BUYER', max_length=15)),
                ('username', models.CharField(db_index=True, max_length=19, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('phone', models.CharField(blank=True, max_length=16, null=True, unique=True)),
                ('is_staff', models.BooleanField(default=False, null=True)),
                ('is_admin', models.BooleanField(default=False, null=True)),
                ('is_superuser', models.BooleanField(default=False, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_mlm_user', models.BooleanField(default=False)),
                ('is_external_user', models.BooleanField(default=False)),
                ('is_account_visible', models.BooleanField(default=True)),
                ('is_account_locked', models.BooleanField(default=False)),
                ('is_account_blocked', models.BooleanField(default=False)),
                ('is_account_deleted', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('last_logout', models.DateTimeField(blank=True, null=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
                ('secret_key', models.BinaryField(max_length=46)),
                ('_pk_hidden', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', accounts.managers.users.CreateUserManager()),
                ('get_by', accounts.managers.users.GetUserManager()),
                ('verify', accounts.managers.users.VerifyUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='BannedEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('datetime_banned', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='BannedPhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=16, unique=True)),
                ('datetime_banned', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='DeviceLoginHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('physical_address', models.JSONField()),
                ('login_at', models.DateTimeField(auto_now_add=True)),
                ('logout_at', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='DeviceTokenBlacklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
            ],
        ),
        migrations.CreateModel(
            name='DeviceWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('synced_amount', models.BinaryField()),
                ('amount_in_sync_transition', models.BinaryField()),
                ('unsynced_amount', models.BinaryField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
            ],
        ),
        migrations.CreateModel(
            name='EmailVerificationOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
            ],
            options={
                'verbose_name': 'Email Verification OTP',
                'verbose_name_plural': 'Email Verification OTPs',
            },
        ),
        migrations.CreateModel(
            name='MLMConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveIntegerField(unique=True)),
                ('commission_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('qualification_sales', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='MLMRelationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='MLMUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referral_code', models.CharField(db_index=True, max_length=255, unique=True)),
                ('level', models.PositiveIntegerField(default=1)),
                ('amount_generated', models.BinaryField()),
                ('children', models.ManyToManyField(related_name='parents', through='accounts.MLMRelationship', to='accounts.mlmuser')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp', models.CharField(max_length=6)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
            ],
            options={
                'verbose_name': 'Phone Number Verification OTP',
                'verbose_name_plural': 'Phone Number Verification OTPs',
            },
        ),
        migrations.CreateModel(
            name='PhoneNumberVerificationOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
                ('current_otp', models.OneToOneField(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.otp')),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=False)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('storage_space', models.DecimalField(decimal_places=2, default=1024.0, max_digits=10)),
                ('consultation_hours', models.DecimalField(decimal_places=2, default=120.0, max_digits=10)),
                ('sale_deduction', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('rental_deduction', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('sales_commission', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('rental_commission', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('new_user_commission', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='UserSubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.CharField(choices=[('MONTHLY', 'monthly'), ('YEARLY', 'yearly'), ('LIFE TIME', 'life time')], default='MONTHLY', max_length=9)),
                ('duration_period', models.PositiveSmallIntegerField(default=1)),
                ('custom_plans', models.ManyToManyField(to='accounts.customplan')),
                ('plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.subscriptionplan')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('STUDENT', 'student'), ('REALTOR', 'realtor'), ('LANDLORD', 'landlord')], default='REALTOR', max_length=10)),
                ('phone', models.CharField(blank=True, max_length=16, null=True, validators=[django.core.validators.MinLengthValidator(8, message="Phone number must be entered in the format: '+999999999'. With a minimum of 8 digits allowed."), django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. From 8 up to 16 digits allowed.", regex='^\\+[0-9]{7,15}$')])),
                ('legal_name', models.CharField(blank=True, max_length=50, null=True)),
                ('gender', models.CharField(choices=[('MALE', 'male'), ('FEMALE', 'female'), ('OTHER', 'other')], default='OTHER', max_length=8)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UsedOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('used_on', models.DateTimeField(auto_now_add=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
                ('email_verification_otp', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.emailverificationotp')),
                ('otp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.otp')),
                ('phone_number_verification_otp', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.phonenumberverificationotp')),
            ],
            options={
                'verbose_name': 'Used OTP',
                'verbose_name_plural': 'Used OTPs',
            },
        ),
        migrations.CreateModel(
            name='RealEstateCertification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='phonenumberverificationotp',
            name='used_otp',
            field=models.ManyToManyField(related_name='phone_number_used_otp', through='accounts.UsedOTP', to='accounts.otp'),
        ),
        migrations.AddField(
            model_name='phonenumberverificationotp',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='MLMUserConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.mlmconfig')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.mlmuser')),
            ],
        ),
        migrations.AddField(
            model_name='mlmrelationship',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child_relationships', to='accounts.mlmuser'),
        ),
        migrations.AddField(
            model_name='mlmrelationship',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_relationships', to='accounts.mlmuser'),
        ),
        migrations.CreateModel(
            name='MLMAchievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('achievement_name', models.CharField(max_length=255)),
                ('achieved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.mlmuser')),
            ],
        ),
        migrations.CreateModel(
            name='KYCVerificationCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_card_verified', models.BooleanField(default=False)),
                ('passport_verified', models.BooleanField(default=False)),
                ('driver_license_verified', models.BooleanField(default=False)),
                ('real_estate_certifications', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.realestatecertification')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'KYC Verification',
                'verbose_name_plural': 'KYC Verifications',
            },
        ),
        migrations.AddField(
            model_name='emailverificationotp',
            name='current_otp',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.otp'),
        ),
        migrations.AddField(
            model_name='emailverificationotp',
            name='used_otp',
            field=models.ManyToManyField(related_name='email_used_otp', through='accounts.UsedOTP', to='accounts.otp'),
        ),
        migrations.AddField(
            model_name='emailverificationotp',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('access_token_expires_at', models.DateTimeField()),
                ('refresh_token_expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
                ('blacklisted_tokens', models.ManyToManyField(to='accounts.devicetokenblacklist')),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_signature', models.BinaryField()),
                ('is_synced', models.BooleanField(default=True)),
                ('device_info', models.TextField()),
                ('trust', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query_id', models.BinaryField(db_index=True, max_length=10000)),
                ('login_history', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.deviceloginhistory')),
                ('tokens', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.devicetoken')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('wallet', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.devicewallet')),
            ],
        ),
        migrations.CreateModel(
            name='AccountVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_verified', models.BooleanField(default=False)),
                ('phone_number_verified', models.BooleanField(default=False)),
                ('score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('kyc_verification_check', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.kycverificationcheck')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Account Verification',
                'verbose_name_plural': 'Account Verifications',
                'ordering': ['-score'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='banned_emails',
            field=models.ManyToManyField(to='accounts.bannedemail'),
        ),
        migrations.AddField(
            model_name='user',
            name='banned_numbers',
            field=models.ManyToManyField(to='accounts.bannedphonenumber'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
