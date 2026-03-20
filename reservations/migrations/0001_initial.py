from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('restaurant', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=120)),
                ('phone', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('party_size', models.PositiveIntegerField()),
                ('reservation_date', models.DateField()),
                ('reservation_time', models.TimeField()),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('confirmed', 'Confirmada'), ('cancelled', 'Cancelada'), ('completed', 'Completada'), ('no_show', 'No asistió')], default='pending', max_length=20)),
                ('attended', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='restaurant.restaurantprofile')),
            ],
        ),
    ]
