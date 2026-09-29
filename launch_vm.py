import os
import oci

REGION = os.environ.get("OCI_REGION", "ap-singapore-1")
TENANCY = os.environ["OCI_TENANCY"]
USER = os.environ["OCI_USER"]
FINGERPRINT = os.environ["OCI_FINGERPRINT"]
PRIVATE_KEY = os.environ["OCI_PRIVATE_KEY"]
SUBNET = os.environ["OCI_SUBNET"]
IMAGE = os.environ["OCI_IMAGE"]
SSH_KEY = os.environ["OCI_SSH_KEY"]
AD = os.environ.get("OCI_AD", "FqdA:AP-SINGAPORE-1-AD-1")
VM_NAME = os.environ.get("VM_NAME", "Tuhinpc-Final-VM")

key_path = "/tmp/oci_api_key.pem"
with open(key_path, "w", encoding="utf-8") as f:
    f.write(PRIVATE_KEY.replace("\\r\\n", "\\n"))
os.chmod(key_path, 0o600)

config = {"user": USER, "fingerprint": FINGERPRINT, "tenancy": TENANCY, "region": REGION, "key_file": key_path}
compute = oci.core.ComputeClient(config)

existing = compute.list_instances(compartment_id=TENANCY, display_name=VM_NAME).data
active = [i for i in existing if i.lifecycle_state not in ("TERMINATED", "TERMINATING")]
if active:
    instance = active[0]
    print(f"VM_EXISTS|{instance.id}|{instance.lifecycle_state}")
    raise SystemExit(0)

details = oci.core.models.LaunchInstanceDetails(
    compartment_id=TENANCY,
    availability_domain=AD,
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=1.0, memory_in_gbs=1.0),
    image_id=IMAGE,
    display_name=VM_NAME,
    create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id=SUBNET, assign_public_ip=True),
    metadata={"ssh_authorized_keys": SSH_KEY},
)

try:
    response = compute.launch_instance(details)
    instance = response.data
    print(f"SUCCESS|{instance.id}|{instance.lifecycle_state}")
except oci.exceptions.ServiceError as exc:
    if exc.status == 500 and exc.code == "InternalError" and "capacity" in str(exc).lower():
        print("CAPACITY_UNAVAILABLE")
        raise SystemExit(2)
    print(f"OCI_ERROR|status={exc.status}|code={exc.code}|message={str(exc.message)[:300]}")
    raise SystemExit(3)
