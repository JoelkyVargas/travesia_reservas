from django.db import migrations, models
import django.core.validators
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='RestaurantProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Travesía', max_length=120)),
                ('short_description', models.CharField(blank=True, max_length=220)),
                ('long_description', models.TextField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('google_maps_url', models.URLField(blank=True)),
                ('whatsapp_number', models.CharField(blank=True, max_length=30)),
                ('primary_color', models.CharField(default='#9f6b3b', max_length=7)),
                ('hero_title', models.CharField(default='Reserva tu mesa en Travesía', max_length=120)),
                ('hero_subtitle', models.CharField(default='Una experiencia gastronómica en La Fortuna.', max_length=220)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='restaurant_assets/')),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='restaurant_assets/')),
                ('menu_pdf', models.FileField(blank=True, null=True, upload_to='menus/')),
                ('regular_capacity_per_slot', models.PositiveIntegerField(default=20)),
                ('slot_minutes', models.PositiveIntegerField(default=60, validators=[django.core.validators.MinValueValidator(15), django.core.validators.MaxValueValidator(240)])),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='BusinessHour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0,'Lunes'),(1,'Martes'),(2,'Miércoles'),(3,'Jueves'),(4,'Viernes'),(5,'Sábado'),(6,'Domingo')])),
                ('opens_at', models.TimeField()),
                ('closes_at', models.TimeField()),
                ('is_open', models.BooleanField(default=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_hours', to='restaurant.restaurantprofile')),
            ],
        ),
        migrations.CreateModel(
            name='BlockedDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('reason', models.CharField(blank=True, max_length=180)),
                ('is_active', models.BooleanField(default=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_dates', to='restaurant.restaurantprofile')),
            ],
            options={'unique_together': {('restaurant', 'date')}},
        ),
        migrations.CreateModel(
            name='BlockedTimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('reason', models.CharField(blank=True, max_length=180)),
                ('is_active', models.BooleanField(default=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_slots', to='restaurant.restaurantprofile')),
            ],
        ),
    ]
