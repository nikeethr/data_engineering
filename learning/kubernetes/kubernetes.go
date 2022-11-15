package main

import (
	cdk "github.com/aws/aws-cdk-go/awscdk/v2"
	ec2 "github.com/aws/aws-cdk-go/awscdk/v2/awsec2"
	eks "github.com/aws/aws-cdk-go/awscdk/v2/awseks"
	"github.com/aws/constructs-go/constructs/v10"
	"github.com/aws/jsii-runtime-go"
)

type StackState struct {
	Stack *cdk.Stack
	Vpc   *ec2.Vpc
	Eks   *eks.Cluster
}

type StackStateMonad struct {
	state *StackState
}

func (s *StackStateMonad) Bind(addToStack func(*StackStateMonad)) *StackStateMonad {
	// unwrap stack and apply function, rebuild monad and return
	addToStack(s)
	return s
}

func (s *StackStateMonad) GetState() *StackState {
	return s.state
}

func declareVPC(mStack *StackStateMonad) {
	state := mStack.GetState()
	vpc := ec2.NewVpc(*state.Stack, jsii.String("KubernetesTestVPC"), &ec2.VpcProps{
		Cidr:        jsii.String("10.0.0.0/21"),
		MaxAzs:      jsii.Number(3),
		NatGateways: jsii.Number(0), // public subnet
		SubnetConfiguration: &[]*ec2.SubnetConfiguration{
			&ec2.SubnetConfiguration{
				SubnetType: ec2.SubnetType_PUBLIC,
				Name:       jsii.String("KubernetesTestSubnet"),
				CidrMask:   jsii.Number(24),
			},
		},
	})
	state.Vpc = &vpc
}

func declareEKS(mStack *StackStateMonad) {
	state := mStack.GetState()
	eks := eks.NewCluster(*state.Stack, jsii.String("KubernetesTestEKS"), &eks.ClusterProps{
		Version:             eks.KubernetesVersion_V1_21(),
		Vpc:                 *state.Vpc,
		DefaultCapacityType: eks.DefaultCapacityType_EC2,
		VpcSubnets: &[]*ec2.SubnetSelection{
			&ec2.SubnetSelection{
				SubnetType: ec2.SubnetType_PUBLIC,
			},
		},
		EndpointAccess: eks.EndpointAccess_PUBLIC(),
	})
	state.Eks = &eks
}

func declareKubernetesStack(
	scope constructs.Construct,
	id *string,
	props *cdk.StackProps,
) func(*StackStateMonad) {
	return func(mStack *StackStateMonad) {
		state := mStack.GetState()
		stack := cdk.NewStack(scope, id, props)
		state.Stack = &stack
	}
}

func main() {
	defer jsii.Close()

	app := cdk.NewApp(nil)
	mStack := &StackStateMonad{
		state: &StackState{
			Stack: nil, Vpc: nil, Eks: nil,
		},
	}

	declareStack := declareKubernetesStack(
		app, jsii.String("KubernetesStack"), &cdk.StackProps{Env: env()},
	)

	mStack.Bind(declareStack).Bind(declareVPC).Bind(declareEKS)

	app.Synth(nil)
}

// env determines the AWS environment (account+region) in which our stack is to
// be deployed. For more information see: https://docs.aws.amazon.com/cdk/latest/guide/environments.html
func env() *cdk.Environment {
	// If unspecified, this stack will be "environment-agnostic".
	// Account/Region-dependent features and context lookups will not work, but a
	// single synthesized template can be deployed anywhere.
	//---------------------------------------------------------------------------
	return nil

	// Uncomment if you know exactly what account and region you want to deploy
	// the stack to. This is the recommendation for production stacks.
	//---------------------------------------------------------------------------
	// return &awscdk.Environment{
	//  Account: jsii.String("123456789012"),
	//  Region:  jsii.String("us-east-1"),
	// }

	// Uncomment to specialize this stack for the AWS Account and Region that are
	// implied by the current CLI configuration. This is recommended for dev
	// stacks.
	//---------------------------------------------------------------------------
	// return &awscdk.Environment{
	//  Account: jsii.String(os.Getenv("CDK_DEFAULT_ACCOUNT")),
	//  Region:  jsii.String(os.Getenv("CDK_DEFAULT_REGION")),
	// }
}
