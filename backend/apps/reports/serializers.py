from rest_framework import serializers


def hours_field() -> serializers.DecimalField:
    return serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


def money_field() -> serializers.DecimalField:
    return serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)


def percentage_field() -> serializers.DecimalField:
    return serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)


class HoursBreakdownSerializer(serializers.Serializer[object]):
    tracked_hours = hours_field()
    billable_hours = hours_field()
    non_billable_hours = hours_field()
    billable_ratio = percentage_field()


class DailyHoursSerializer(serializers.Serializer[object]):
    day = serializers.DateField(read_only=True)
    billable_hours = hours_field()
    non_billable_hours = hours_field()


class GroupHoursSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    tracked_hours = hours_field()
    billable_hours = hours_field()


class CurrencyRevenueSerializer(serializers.Serializer[object]):
    currency = serializers.CharField(read_only=True)
    draft = money_field()
    invoiced = money_field()
    paid = money_field()
    outstanding = money_field()


class RetainerUsageSerializer(serializers.Serializer[object]):
    client_id = serializers.IntegerField(read_only=True)
    client_name = serializers.CharField(read_only=True)
    currency = serializers.CharField(read_only=True)
    included_hours = hours_field()
    rollover_hours = hours_field()
    used_hours = hours_field()
    remaining_hours = hours_field()
    overage_hours = hours_field()
    utilization = percentage_field()
    projected_total = money_field()
    invoice_id = serializers.IntegerField(read_only=True, allow_null=True)
    invoice_status = serializers.CharField(read_only=True, allow_null=True)


class OverviewSerializer(serializers.Serializer[object]):
    period = serializers.CharField(read_only=True)
    hours = HoursBreakdownSerializer(read_only=True)
    unbilled_hours = hours_field()
    active_timers = serializers.IntegerField(read_only=True)
    revenue = CurrencyRevenueSerializer(many=True, read_only=True)
    daily = DailyHoursSerializer(many=True, read_only=True)
    members = GroupHoursSerializer(many=True, read_only=True)
    clients = GroupHoursSerializer(many=True, read_only=True)


class RetainerReportSerializer(serializers.Serializer[object]):
    period = serializers.CharField(read_only=True)
    retainers = RetainerUsageSerializer(many=True, read_only=True)


class MyTimeSerializer(serializers.Serializer[object]):
    period = serializers.CharField(read_only=True)
    hours = HoursBreakdownSerializer(read_only=True)
    daily = DailyHoursSerializer(many=True, read_only=True)
    projects = GroupHoursSerializer(many=True, read_only=True)
